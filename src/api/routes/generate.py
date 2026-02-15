"""
Generate route handlers
Handles L5X code generation from parsed CSV using RAG pipeline
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from typing import Dict
from src.core.l5x.pipeline import L5XGenerationPipeline
from src.core.parser.csv_parser import parse_csv_file
from src.config.constants import MAX_CSV_SIZE
from src.utils.logger import logger

router = APIRouter()

# Initialize pipeline (singleton pattern)
_pipeline = None

def get_pipeline() -> L5XGenerationPipeline:
    """Get or create pipeline instance"""
    global _pipeline
    if _pipeline is None:
        _pipeline = L5XGenerationPipeline()
    return _pipeline


@router.post("/generate")
async def generate_l5x_from_csv(
    file: UploadFile = File(...),
    machine_index: int = 0
) -> Dict:
    """
    Generate L5X code from CSV file using new L5X pipeline with RAG

    Args:
        file: CSV file containing PLC logic
        machine_index: Which machine to generate (default: 0 = first)

    Returns:
        Dictionary with generated L5X code and metadata
    """
    # Validate file
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )

    logger.info(f"Generating L5X for {file.filename}, machine index: {machine_index}")

    try:
        # Read CSV
        contents = await file.read()

        if len(contents) > MAX_CSV_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_CSV_SIZE / 1024 / 1024}MB"
            )

        csv_content = contents.decode('utf-8')

        # Parse CSV first to get machine name
        parsed_csv = parse_csv_file(csv_content)

        if parsed_csv.total_machines == 0:
            raise HTTPException(
                status_code=400,
                detail="No machines found in CSV"
            )

        if machine_index >= parsed_csv.total_machines:
            raise HTTPException(
                status_code=400,
                detail=f"Machine index {machine_index} out of range (found {parsed_csv.total_machines} machines)"
            )

        machine_name = parsed_csv.machines[machine_index].name

        # Run new L5X generation pipeline with RAG
        pipeline = get_pipeline()
        result = pipeline.generate_from_csv(
            csv_content=csv_content,
            project_name=f"{machine_name}_Project",
            validate_output=True
        )

        l5x_code = result['l5x_content']
        validation = result.get('validation', {})
        statistics = result.get('statistics', {})

        is_valid = validation.get('valid', False) if validation else False
        issues = validation.get('issues', []) if validation else []
        warnings = validation.get('warnings', []) if validation else []

        logger.info(f"Successfully generated L5X for {machine_name} "
                   f"({len(l5x_code)} characters, valid: {is_valid})")

        return {
            "status": "success",
            "machine_name": machine_name,
            "l5x_code": l5x_code,
            "code_length": len(l5x_code),
            "similar_count": 0,  # TODO: Add RAG retrieval count
            "validation": {
                "is_valid": is_valid,
                "issues": issues,
                "warnings": warnings
            },
            "statistics": statistics
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Could not decode CSV file. Ensure it's UTF-8 encoded."
        )

    except Exception as e:
        logger.error(f"Generation error: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/generate-refined")
async def generate_l5x_with_refinement(
    file: UploadFile = File(...),
    machine_index: int = 0,
    max_iterations: int = 3
) -> Dict:
    """
    Generate L5X code with iterative refinement to fix validation issues

    NOTE: Currently uses the new pipeline which has built-in retry logic.
    Future enhancement: Add iterative refinement loop.

    Args:
        file: CSV file containing PLC logic
        machine_index: Which machine to generate (default: 0 = first)
        max_iterations: Maximum refinement iterations (default: 3, max: 5)

    Returns:
        Dictionary with generated L5X code, validation results, and iteration history
    """
    # For now, delegate to the regular generate function
    # The new pipeline has retry logic built into routine generation
    logger.info(f"Generating L5X with refinement for {file.filename}, "
               f"machine index: {machine_index}")

    result = await generate_l5x_from_csv(file, machine_index)

    # Add refinement metadata (placeholder for future enhancement)
    result["refinement"] = {
        "iterations": [],
        "total_iterations": 0,
        "final_valid": result["validation"]["is_valid"],
        "note": "Using new pipeline with built-in retry logic per routine"
    }

    return result


@router.post("/generate-from-file")
async def generate_from_uploaded_file(
    file: UploadFile = File(...),
    machine_index: int = 0
) -> Dict:
    """
    Simpler endpoint that matches the UI workflow better

    Args:
        file: CSV file (can be re-uploaded original or blob from UI)
        machine_index: Which machine to generate

    Returns:
        Generation results
    """
    logger.info(f"Generate from file: {file.filename}, machine_index: {machine_index}")

    try:
        # Read the file content
        contents = await file.read()

        # Try to decode as CSV text
        try:
            csv_content = contents.decode('utf-8')
        except:
            raise HTTPException(status_code=400, detail="Could not decode file as UTF-8 text")

        # Parse CSV first to get machine name
        parsed_csv = parse_csv_file(csv_content)

        if parsed_csv.total_machines == 0:
            raise HTTPException(status_code=400, detail="No machines found in CSV")

        if machine_index >= parsed_csv.total_machines:
            raise HTTPException(
                status_code=400,
                detail=f"Machine index {machine_index} out of range (found {parsed_csv.total_machines} machines)"
            )

        machine_name = parsed_csv.machines[machine_index].name

        # Run pipeline
        pipeline = get_pipeline()
        result = pipeline.generate_from_csv(
            csv_content=csv_content,
            project_name=f"{machine_name}_Project",
            validate_output=True
        )

        l5x_code = result['l5x_content']
        validation = result.get('validation', {})
        statistics = result.get('statistics', {})

        return {
            "status": "success",
            "machine_name": machine_name,
            "l5x_code": l5x_code,
            "code_length": len(l5x_code),
            "validation": {
                "is_valid": validation.get('valid', False),
                "issues": validation.get('issues', []),
                "warnings": validation.get('warnings', [])
            },
            "statistics": statistics
        }

    except Exception as e:
        logger.error(f"Generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-download")
async def generate_and_download(
    file: UploadFile = File(...),
    machine_index: int = 0
) -> Response:
    """
    Generate L5X and return as downloadable file

    Args:
        file: CSV file containing PLC logic
        machine_index: Which machine to generate

    Returns:
        L5X file as attachment
    """
    # Generate L5X
    result = await generate_l5x_from_csv(file, machine_index)

    if result["status"] != "success":
        raise HTTPException(
            status_code=500,
            detail="Generation failed"
        )

    # Create filename
    machine_name = result["machine_name"].replace(" ", "_")
    filename = f"{machine_name}.L5X"

    # Return as download
    return Response(
        content=result["l5x_code"],
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
