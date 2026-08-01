from pathlib import Path
from config.config import *
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from markitdown import MarkItDown
import pandas as pd

from src.ingestion.clean import clean_text

_md = None
SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"}


def get_markitdown():
    global _md
    if _md is None:
        _md = MarkItDown()
    return _md


def load_excel(file_path):
    documents = []
    sheets = pd.read_excel(file_path, sheet_name=None, header=None)

    for sheet_name, df in sheets.items():
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        df = df.fillna("")

        header_row = None

        for i in range(len(df)):
            values = df.iloc[i].astype(str).tolist()
            non_empty = sum(
                value.strip() not in ("", "nan")
                for value in values
            )

            if non_empty >= 3:
                header_row = i
                break

        if header_row is None:
            continue

        df.columns = df.iloc[header_row]
        df.columns = [
            str(col).replace("\n", " ").strip()
            for col in df.columns
        ]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        for row_number, (_, row) in enumerate(df.iterrows()):
            text = "\n".join(
                f"{column}: {row[column]}"
                for column in df.columns
            )

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": file_path.name,
                        "sheet": sheet_name,
                        "row": row_number,
                        "chunk_id": row_number,
                        "file_type": ".xlsx"
                    }
                )
            )

    return documents


def load_documents(dataset_dir=None):
    documents = []

    if dataset_dir is None:
        raise ValueError("dataset_dir must be provided")

    for file_path in Path(dataset_dir).iterdir():
        if file_path.suffix.lower() not in SUPPORTED:
            continue

        try:
            if file_path.suffix.lower() == ".xlsx":
                documents.extend(load_excel(file_path))
            else:
                result = get_markitdown().convert(file_path)
                text = clean_text(result.text_content)

                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": file_path.name,
                            "file_type": file_path.suffix.lower()
                        }
                    )
                )

        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")

    return documents


# chunking
def split_documents(documents):
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks = []
    for doc in documents:
        if doc.metadata.get("file_type") == ".xlsx":
            chunks.append(doc)
            continue

        split_chunks = recursive_splitter.split_documents([doc])

        for i, chunk in enumerate(split_chunks):
            chunk.metadata["chunk_id"] = i

        chunks.extend(split_chunks)

    return chunks
    