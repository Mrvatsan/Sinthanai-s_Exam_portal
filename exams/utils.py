import pandas as pd
import os
import io

def clean_and_parse_excel(file_obj):
    """
    Parses an uploaded Excel file (xlsx, xls, HTML content in xls).
    Returns a pandas DataFrame with standardized columns.
    """
    import logging
    import xlrd
    from io import BytesIO
    
    # Use relative path for debug log that works on both Windows and Linux
    log_file = os.path.join(os.path.dirname(__file__), '..', 'debug.log')
    try:
        logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                           format='%(asctime)s - %(message)s')
    except:
        # If file logging fails, just use console logging
        logging.basicConfig(level=logging.DEBUG, 
                           format='%(asctime)s - %(message)s')
    
    df = None
    excel_error = None
    html_error = None
    
    # Get file name to determine type
    file_name = getattr(file_obj, 'name', '')
    logging.debug(f"Processing file: {file_name}")
    print(f"DEBUG: Processing file: {file_name}")
    
    # Read first few bytes to check content type
    file_obj.seek(0)
    first_bytes = file_obj.read(500)
    file_obj.seek(0)
    
    logging.debug(f"First 500 bytes: {first_bytes}")
    print(f"DEBUG: First 200 chars of file: {first_bytes[:200]}")
    
    is_html = b'<html' in first_bytes.lower() or b'<table' in first_bytes.lower() or b'<?xml' in first_bytes.lower()
    
    # Strategy 1: Try HTML parsing first if HTML detected
    if is_html:
        logging.debug("Detected HTML/XML content")
        print(f"DEBUG: Detected HTML/XML content in file")
        for engine in ['lxml', 'html5lib', 'bs4']:
            try:
                file_obj.seek(0)
                dfs = pd.read_html(file_obj, flavor=engine)
                if dfs and len(dfs) > 0:
                    df = dfs[0]
                    logging.debug(f"Successfully read HTML with {engine}: {len(df)} rows, {len(df.columns)} cols")
                    print(f"DEBUG: Successfully read HTML table with engine '{engine}': {len(df)} rows, {len(df.columns)} columns")
                    break
            except Exception as e:
                logging.debug(f"HTML read with {engine} failed: {str(e)}")
                print(f"DEBUG: HTML read with {engine} failed: {str(e)}")
                html_error = str(e)
    
    # Strategy 2: Try standard Excel parsing if not HTML or if HTML failed
    if df is None:
        logging.debug("Trying Excel parsing")
        try:
            file_obj.seek(0)
            if file_name.endswith('.xlsx'):
                df = pd.read_excel(file_obj, engine='openpyxl')
            elif file_name.endswith('.xls'):
                # For .xls files, try direct xlrd parsing with forgiving options
                try:
                    file_obj.seek(0)
                    file_contents = file_obj.read()
                    workbook = xlrd.open_workbook(file_contents=file_contents, 
                                                 formatting_info=False,
                                                 on_demand=True,
                                                 ignore_workbook_corruption=True)
                    sheet = workbook.sheet_by_index(0)
                    
                    # Convert to list of lists
                    data = []
                    for row_idx in range(sheet.nrows):
                        row = []
                        for col_idx in range(sheet.ncols):
                            cell = sheet.cell(row_idx, col_idx)
                            row.append(cell.value)
                        data.append(row)
                    
                    # Create DataFrame
                    if len(data) > 0:
                        df = pd.DataFrame(data[1:], columns=data[0])
                        logging.debug(f"Successfully read XLS with direct xlrd: {len(df)} rows, {len(df.columns)} cols")
                        print(f"DEBUG: Successfully read XLS with direct xlrd: {len(df)} rows, {len(df.columns)} columns")
                except Exception as xlrd_err:
                    logging.debug(f"Direct xlrd failed: {str(xlrd_err)}")
                    print(f"DEBUG: Direct xlrd failed: {str(xlrd_err)}")
                    raise xlrd_err
            else:
                # Try openpyxl first, then xlrd
                try:
                    df = pd.read_excel(file_obj, engine='openpyxl')
                except:
                    file_obj.seek(0)
                    df = pd.read_excel(file_obj, engine='xlrd')
            
            if df is not None:
                logging.debug(f"Successfully read Excel: {len(df)} rows, {len(df.columns)} cols")
                print(f"DEBUG: Successfully read Excel file: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            excel_error = str(e)
            logging.debug(f"Excel read failed: {excel_error}")
            print(f"DEBUG: Excel read failed: {excel_error}")

    if df is None:
        error_msg = f"Could not parse file. Ensure it is a valid Excel or HTML table file. Excel error: {excel_error}, HTML error: {html_error}"
        logging.debug(error_msg)
        print(f"DEBUG: {error_msg}")
        raise ValueError(error_msg)

    # Standardize Column Names - convert to lowercase for matching
    df.columns = df.columns.astype(str).str.lower().str.strip().str.replace(r'\s+', '', regex=True)
    
    print(f"DEBUG: Detected Columns in file: {list(df.columns)}")

    # Robust Fuzzy Mapping
    # We iterate over columns and try to match them to expected fields
    
    normalization_map = {}
    
    for col in df.columns:
        # Register No Matching - handle 'registerno', 'register_no', 'regno', etc.
        if 'register' in col or col == 'regno' or col == 'registerno':
            normalization_map[col] = 'register_no'
        elif 'rollno' in col or col == 'roll':
            normalization_map[col] = 'register_no'
            
        # Name Matching - handle 'studentname', 'name', 'student_name'
        elif ('student' in col and 'name' in col) or (col == 'name' or col == 'studentname'):
            normalization_map[col] = 'name'
            
        # Course Code - handle 'coursecode', 'course_code', 'subjectcode'
        elif 'coursecode' in col or 'subjectcode' in col or 'subcode' in col:
             normalization_map[col] = 'course_code'
             
        # Course Title - handle 'coursetitle', 'course_title', 'subjecttitle'
        elif 'coursetitle' in col or 'subjecttitle' in col or 'subjecttname' in col:
             normalization_map[col] = 'course_title'
             
        # Hall - handle 'examhallnumber', 'hallno', 'hall_no', 'room'
        elif 'hall' in col or 'room' in col:
            normalization_map[col] = 'hall_no'
            
        # Seat - handle 'examseatnumber', 'seatno', 'seat_no'
        elif 'seat' in col:
            normalization_map[col] = 'seat_no'
            
        # Session - handle 'examsession', 'session'
        elif 'session' in col:
             normalization_map[col] = 'session'
             
        # Date - handle 'examdate', 'exam_date', 'date'
        elif 'examdate' in col or (col == 'date'):
            normalization_map[col] = 'exam_date'

    # Apply mapping
    df = df.rename(columns=normalization_map)
    print(f"DEBUG: Mapped Columns: {list(df.columns)}")

    # Check for critical column
    if 'register_no' not in df.columns:
        # Fallback: if 'register_no' is missing but we have column 0, maybe use that? 
        # No, that's too risky.
        raise ValueError(f"Could not find 'Register No' column. Found columns: {list(df.columns)}")
        
    df = df.dropna(subset=['register_no'])
         
    return df
