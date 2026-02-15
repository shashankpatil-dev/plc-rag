"""
Upload route handlers
Handles CSV file uploads and parsing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.models.csv_models import UploadResponse, ParsedCSV
from src.core.parser.csv_parser import parse_csv_bytes, CSVParserError
from src.config.constants import MAX_CSV_SIZE
from src.utils.logger import logger

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload and parse CSV logic sheet

    Args:
        file: CSV file containing PLC logic definitions

    Returns:
        UploadResponse with parsed data and status

    Raises:
        HTTPException: If file is invalid or parsing fails
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file with .csv extension"
        )

    logger.info(f"Received CSV upload: {file.filename}")

    try:
        # Read file content
        contents = await file.read()

        # Check file size
        if len(contents) > MAX_CSV_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_CSV_SIZE / 1024 / 1024}MB"
            )

        # Parse CSV
        parsed_data = parse_csv_bytes(contents)

        logger.info(
            f"Successfully parsed {file.filename}: "
            f"{parsed_data.total_machines} machines, {parsed_data.total_states} states"
        )

        return UploadResponse(
            status="success",
            message=f"Successfully parsed {parsed_data.total_machines} machine(s)",
            filename=file.filename,
            parsed_data=parsed_data
        )

    except CSVParserError as e:
        logger.error(f"CSV parsing error for {file.filename}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"CSV parsing failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/parse-csv", response_model=ParsedCSV)
async def parse_csv_endpoint(file: UploadFile = File(...)) -> ParsedCSV:
    """
    Parse CSV and return structured data only (no wrapper)

    Simpler endpoint that directly returns the parsed CSV structure
    without the UploadResponse wrapper.

    Args:
        file: CSV file containing PLC logic definitions

    Returns:
        ParsedCSV object with all machines and states

    Raises:
        HTTPException: If file is invalid or parsing fails
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )

    try:
        # Read and parse
        contents = await file.read()

        if len(contents) > MAX_CSV_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_CSV_SIZE / 1024 / 1024}MB"
            )

        parsed_data = parse_csv_bytes(contents)
        logger.info(f"Parsed {file.filename}: {parsed_data.summary()}")

        return parsed_data

    except CSVParserError as e:
        logger.error(f"CSV parsing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
