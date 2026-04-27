import os


DATA_PATH = "data"
RAW_DATA_FOLDER = "data_original"
PROCESSED_DATA_FOLDER = "outputs"
ANALYSIS_DATA_FOLDER = "analysis"
METADATA_FOLDER = "metadata"
LOGS_FOLDER = "logs"
SUMMARIES_FOLDER = "resumenes"
LOG_EXTENSION = ".log"
SUMMARY_EXTENSION = ".csv"
PARQUET_EXTENSION = ".parquet"


def get_raw_phase_path(fase):
    return os.path.join(DATA_PATH, RAW_DATA_FOLDER, fase)


def get_processed_output_path(fase):
    return os.path.join(DATA_PATH, PROCESSED_DATA_FOLDER, f"{fase}{PARQUET_EXTENSION}")


def get_analysis_output_path(nombre):
    return os.path.join(DATA_PATH, ANALYSIS_DATA_FOLDER, f"{nombre}{PARQUET_EXTENSION}")


def get_metadata_path(nombre):
    return os.path.join(DATA_PATH, METADATA_FOLDER, nombre)


def get_log_path(fase):
    return os.path.join(DATA_PATH, LOGS_FOLDER, f"{fase}{LOG_EXTENSION}")


def get_summary_path(fase):
    return os.path.join(DATA_PATH, SUMMARIES_FOLDER, f"{fase}{SUMMARY_EXTENSION}")
