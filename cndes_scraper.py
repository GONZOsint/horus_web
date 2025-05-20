import re
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging
import requests
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse Spanish date format to datetime object."""
    try:
        if not date_str or not isinstance(date_str, str):
            logger.warning(f"Invalid date string: {date_str}")
            return None
            
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Clean the date string
        date_str = date_str.lower().strip()
        logger.info(f"Attempting to parse date string: '{date_str}'")
        
        # Try parsing the CNDES format first (e.g., "Sun, 17 May 2009 00:00:00 GM")
        try:
            parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            logger.info(f"Successfully parsed CNDES date format: {parsed_date}")
            return parsed_date
        except ValueError:
            logger.info("CNDES format parsing failed, trying Spanish format")
        
        # Try Spanish format: "DD de MMMM de YYYY"
        match = re.match(r'(\d+)\s+de\s+(\w+)\s+de\s+(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            logger.info(f"Date components - Day: {day}, Month: {month}, Year: {year}")
            
            if month in months:
                month_num = months[month]
                logger.info(f"Converted month '{month}' to number: {month_num}")
                try:
                    parsed_date = datetime(int(year), month_num, int(day))
                    logger.info(f"Successfully parsed date: {parsed_date}")
                    return parsed_date
                except ValueError as e:
                    logger.error(f"Invalid date values - Day: {day}, Month: {month_num}, Year: {year}: {str(e)}")
            else:
                logger.warning(f"Unknown month: {month}")
        else:
            logger.warning(f"Date string does not match expected format: {date_str}")
            logger.warning("Expected format: 'DD de MMMM de YYYY' (e.g., '15 de enero de 2024')")
                
        logger.warning(f"Could not parse date string: {date_str}")
        return None
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {str(e)}")
        return None

def extract_age(age_str: str) -> Optional[int]:
    """Extract age number from string like '17 años'."""
    try:
        if not age_str or not isinstance(age_str, str):
            logger.warning(f"Invalid age string: {age_str}")
            return None
            
        logger.info(f"Attempting to extract age from: '{age_str}'")
        match = re.search(r'(\d+)\s*años', age_str)
        if match:
            age = int(match.group(1))
            logger.info(f"Extracted age: {age}")
            if age < 0 or age > 120:  # Reasonable age range check
                logger.warning(f"Unusual age value: {age}")
            return age
        logger.warning(f"Could not extract age from: {age_str}")
        return None
    except Exception as e:
        logger.error(f"Error extracting age from '{age_str}': {str(e)}")
        return None

def extract_weight(description: str) -> Optional[int]:
    """Extract weight from description text like 'PESA 110 KG'."""
    try:
        if not description or not isinstance(description, str):
            logger.warning(f"Invalid description string: {description}")
            return None
            
        logger.info(f"Attempting to extract weight from: '{description}'")
        match = re.search(r'PESA\s+(\d+)\s*KG', description, re.IGNORECASE)
        if match:
            weight = int(match.group(1))
            logger.info(f"Extracted weight: {weight}")
            if weight < 0 or weight > 500:  # Reasonable weight range check
                logger.warning(f"Unusual weight value: {weight}")
            return weight
        logger.warning(f"Could not extract weight from: {description}")
        return None
    except Exception as e:
        logger.error(f"Error extracting weight from '{description}': {str(e)}")
        return None

def extract_details_from_description(description: str) -> Dict:
    """Extract additional details from the description text."""
    details = {}
    try:
        if not description:
            logger.warning("Empty description provided")
            return details
            
        logger.info("Extracting details from description")
        
        # Extract height
        height_match = re.search(r'MIDE\s+(\d+[.,]\d+)', description, re.IGNORECASE)
        if height_match:
            try:
                height = float(height_match.group(1).replace(',', '.'))
                details['height'] = height
                logger.info(f"Extracted height: {height}")
            except ValueError:
                logger.warning(f"Could not parse height: {height_match.group(1)}")
                
        # Extract weight
        weight_match = re.search(r'PESA\s+(\d+)\s*KG', description, re.IGNORECASE)
        if weight_match:
            try:
                weight = int(weight_match.group(1))
                details['weight'] = weight
                logger.info(f"Extracted weight: {weight}")
            except ValueError:
                logger.warning(f"Could not parse weight: {weight_match.group(1)}")
                
        # Extract last seen clothing
        clothing_match = re.search(r'VESTÍA\s+(.*?)(?:\.|$)', description, re.IGNORECASE)
        if clothing_match:
            details['last_seen_clothing'] = clothing_match.group(1).strip()
            logger.info(f"Extracted clothing: {details['last_seen_clothing']}")
            
        return details
    except Exception as e:
        logger.error(f"Error extracting details from description: {str(e)}")
        return details

def scrape_cndes_case(desaparecido_id: str) -> Tuple[Dict, bool, str]:
    """
    Scrape case information from CNDES detail page.
    
    Args:
        desaparecido_id (str): ID of the missing person case or full URL
        
    Returns:
        Tuple containing:
        - Dict with parsed case information
        - bool indicating success
        - str with error message if any
    """
    try:
        print("\n=== Starting CNDES Case Scraping ===")
        print(f"Processing input: {desaparecido_id}")
        
        if not desaparecido_id or not isinstance(desaparecido_id, str):
            print("❌ Error: Invalid input provided")
            logger.error("Invalid input provided")
            return {}, False, "Invalid input provided"
            
        # Extract case ID from URL if a full URL is provided
        if desaparecido_id.startswith('http'):
            try:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(desaparecido_id)
                query_params = parse_qs(parsed_url.query)
                if 'desaparecido' not in query_params:
                    print("❌ Error: No case ID found in URL")
                    logger.error("No case ID found in URL")
                    return {}, False, "No case ID found in URL"
                desaparecido_id = query_params['desaparecido'][0]
                logger.info(f"Extracted case ID from URL: {desaparecido_id}")
            except Exception as e:
                print(f"❌ Error parsing URL: {str(e)}")
                logger.error(f"Error parsing URL: {str(e)}")
                return {}, False, f"Error parsing URL: {str(e)}"
            
        # Normalize the case ID to match the format in the HAR log
        desaparecido_id = desaparecido_id.strip().upper()  # Convert to uppercase as shown in HAR log
        if not re.match(r'^[A-F0-9]{32}$', desaparecido_id):
            print(f"❌ Error: Invalid case ID format: {desaparecido_id}")
            logger.error(f"Invalid case ID format: {desaparecido_id}")
            return {}, False, f"Invalid case ID format: {desaparecido_id}"
            
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Set initial cookies exactly as in the HAR log
        session.cookies.set(
            "JSESSIONID", 
            "\"-CFVVTmNpHvosUK-nqeAPh-SWdgqHlDPJyVrFEf1.master:APP_PUBLICO\"",
            domain="cndes-web.ses.mir.es",
            path="/"
        )
        session.cookies.set(
            "accept_cookies_desaparecidos",
            "no",
            domain="cndes-web.ses.mir.es",
            path="/"
        )
        
        # Configure session to maintain cookies
        session.trust_env = False  # Don't use environment variables
        session.verify = True  # Verify SSL certificates
        
        # Base headers that will be used across requests
        base_headers = {
            "Host": "cndes-web.ses.mir.es",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept-Language": "es,es-ES;q=0.8,en;q=0.5,en-US;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Referer": f"https://cndes-web.ses.mir.es/publico/Desaparecidos/Detalle-Desaparecido?desaparecido={desaparecido_id}",
            "Strict-Transport-Security": "max-age=63072000; includeSubdomains",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block"
        }
        
        # Step 1: Get the base properties file
        print("\n📡 Getting base properties...")
        properties_url = "https://cndes-web.ses.mir.es/publico/Desaparecidos/.resources/desaparecidos-plantilla/webresources/i18n/Desaparecidos.properties"
        properties_headers = {
            **base_headers,
            "Accept": "text/plain, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        try:
            response = session.get(
                properties_url,
                headers=properties_headers,
                params={"_": int(datetime.now().timestamp() * 1000)},
                verify=True
            )
            if response.status_code != 200:
                print(f"❌ Error: Properties request failed with status code {response.status_code}")
                logger.error(f"Properties request failed with status code {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}")
                return {}, False, f"Properties request failed with status code {response.status_code}"
                
            # Update JSESSIONID if a new one is provided
            if 'JSESSIONID' in response.cookies:
                session.cookies.set('JSESSIONID', response.cookies['JSESSIONID'], domain="cndes-web.ses.mir.es")
                
        except Exception as e:
            print(f"❌ Error getting properties: {str(e)}")
            logger.error(f"Error getting properties: {str(e)}")
            return {}, False, f"Error getting properties: {str(e)}"
            
        # Step 2: Get the Spanish properties file
        print("\n📡 Getting Spanish properties...")
        es_properties_url = "https://cndes-web.ses.mir.es/publico/Desaparecidos/.resources/desaparecidos-plantilla/webresources/i18n/Desaparecidos_es.properties"
        
        try:
            response = session.get(
                es_properties_url,
                headers=properties_headers,
                params={"_": int(datetime.now().timestamp() * 1000)},
                verify=True
            )
            if response.status_code != 200:
                print(f"❌ Error: Spanish properties request failed with status code {response.status_code}")
                logger.error(f"Spanish properties request failed with status code {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}")
                return {}, False, f"Spanish properties request failed with status code {response.status_code}"
        except Exception as e:
            print(f"❌ Error getting Spanish properties: {str(e)}")
            logger.error(f"Error getting Spanish properties: {str(e)}")
            return {}, False, f"Error getting Spanish properties: {str(e)}"
            
        # Step 3: Get the case details
        print("\n📡 Getting case details...")
        details_url = "https://cndes-web.ses.mir.es/publico/Desaparecidos/dao/ServletDesaparecidos"
        details_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept": "*/*",
            "Accept-Language": "es,es-ES;q=0.8,en;q=0.5,en-US;q=0.3",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": f"https://cndes-web.ses.mir.es/publico/Desaparecidos/Detalle-Desaparecido?desaparecido={desaparecido_id}"
        }
        
        # Prepare the form data exactly as in the HAR log
        form_data = {
            "operacion": "cargarDetalle",
            "locale": "es",
            "idDesaparecido": desaparecido_id.lower()  # Convert to lowercase for the API request
        }
        
        try:
            # Log the request details for debugging
            logger.info(f"Making POST request to {details_url}")
            logger.info(f"Headers: {details_headers}")
            logger.info(f"Form data: {form_data}")
            
            # Convert form data to URL-encoded string exactly as in HAR log
            encoded_data = "&".join([f"{k}={v}" for k, v in form_data.items()])
            logger.info(f"Encoded form data: {encoded_data}")
            
            response = session.post(
                details_url,
                headers=details_headers,
                data=encoded_data,
                verify=True,
                allow_redirects=True  # Allow redirects to maintain session
            )
            
            if response.status_code != 200:
                print(f"❌ Error: Details request failed with status code {response.status_code}")
                logger.error(f"Details request failed with status code {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}")
                return {}, False, f"Details request failed with status code {response.status_code}"
            
            # Log response details for debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response encoding: {response.encoding}")
            logger.info(f"Response content type: {response.headers.get('Content-Type', '')}")
            
            # Ensure proper encoding
            response.encoding = 'utf-8'
            
            # Parse JSON response
            try:
                # Log raw response for debugging
                logger.info(f"Raw response text: {response.text[:1000]}")
                
                data = response.json()
                logger.info(f"Parsed JSON data: {json.dumps(data, indent=2)[:1000]}")
                
                if not data or 'desaparecido' not in data or not data['desaparecido']:
                    print("❌ Error: Invalid response format")
                    logger.error("Invalid response format")
                    logger.error(f"Response content: {response.text[:500]}")
                    return {}, False, "Invalid response format"
                    
                case_data = data['desaparecido'][0]
                logger.info(f"Processing case data: {json.dumps(case_data, indent=2)}")
                
                # Map gender values from CNDES to our system
                gender_mapping = {
                    'HOMBRE': 'MALE',
                    'MUJER': 'FEMALE',
                    'VARÓN': 'MALE',
                    'VARON': 'MALE',
                    'MASCULINO': 'MALE',
                    'FEMENINO': 'FEMALE',
                    'OTRO': 'OTHER',
                    'NO ESPECIFICADO': 'OTHER',
                    'HOMBRE': 'MALE',  # Handle case with capital H
                    'MUJER': 'FEMALE'  # Handle case with capital M
                }
                
                # Log the raw gender value from CNDES
                raw_gender = case_data.get('genero', '')
                logger.info(f"Raw gender value from CNDES: '{raw_gender}'")
                
                # Log all available fields from CNDES for debugging
                logger.info("Available fields from CNDES:")
                for key, value in case_data.items():
                    logger.info(f"{key}: {value}")
                
                # Extract and process data
                processed_data = {
                    'cndes_id': case_data.get('id'),
                    'title': case_data.get('nombreCompleto'),
                    'description': case_data.get('resumenWeb'),
                    'disappearance_date': parse_date(case_data.get('fechaDesaparicion')),
                    'birth_date': parse_date(case_data.get('fechaNacimiento')),
                    'age_at_disappearance': extract_age(case_data.get('edad')),
                    'current_age': extract_age(case_data.get('edadActual')),
                    'disappearance_location': case_data.get('lugarDesaparicion', '').replace('<strong id=\'localidad\'>', '').replace('</strong>', ''),
                    'gender': gender_mapping.get(raw_gender.upper(), 'OTHER'),
                    'eye_color': case_data.get('colorOjos'),
                    'hair_color': case_data.get('colorPelo'),
                    'hair_type': case_data.get('tipoPelo'),
                    'hair_length': case_data.get('longCabello'),
                    'body_type': case_data.get('constitucion'),
                    'height': case_data.get('altura'),
                    'weight': extract_weight(case_data.get('resumenWeb')),  # Extract weight from description
                    'contact_body': case_data.get('cuerpo'),
                    'contact_phone': case_data.get('telefono'),
                    'is_minor': case_data.get('tipoDesaparecido') == 'MENOR',
                    'photo': case_data.get('foto'),
                    # Additional fields from CNDES
                    'first_name': case_data.get('nombre'),
                    'last_name1': case_data.get('apellido1'),
                    'last_name2': case_data.get('apellido2'),
                    'is_found': case_data.get('localizado') == '1',
                    'needs': case_data.get('necesidades'),
                    'disappearance_type': 'INVOLUNTARY' if case_data.get('tipoDesaparecido') == 'ADULTO' else 'UNKNOWN'
                }
                
                # Log the mapped gender value
                logger.info(f"Mapped gender value: '{processed_data['gender']}'")
                
                # Extract additional details from description
                if processed_data.get('description'):
                    additional_details = extract_details_from_description(processed_data['description'])
                    processed_data.update(additional_details)
                    logger.info(f"Additional details from description: {json.dumps(additional_details, indent=2)}")
                
                # Log all available fields from CNDES
                logger.info("Available fields from CNDES:")
                for key, value in case_data.items():
                    logger.info(f"{key}: {value}")
                
                # Log the processed data
                logger.info(f"Processed data: {json.dumps(processed_data, indent=2, default=str)}")
                
                # Validate the data
                if not validate_cndes_data(processed_data):
                    missing_fields = [field for field in ['title', 'disappearance_date', 'birth_date', 
                                                        'age_at_disappearance', 'current_age', 
                                                        'disappearance_location'] 
                                    if not processed_data.get(field)]
                    error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                    print(f"❌ Validation error: {error_msg}")
                    logger.error(f"Missing required fields: {missing_fields}")
                    logger.error(f"Available fields: {list(processed_data.keys())}")
                    return processed_data, False, error_msg
                    
                print("\n✨ Successfully scraped and validated case data")
                return processed_data, True, ""
                
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON response: {str(e)}")
                logger.error(f"Error parsing JSON response: {str(e)}")
                logger.error(f"Response content: {response.text[:500]}")
                return {}, False, f"Error parsing JSON response: {str(e)}"
                
        except Exception as e:
            print(f"\n❌ Error in scrape_cndes_case: {str(e)}")
            logger.error(f"Error in scrape_cndes_case: {str(e)}")
            return {}, False, str(e)
            
    except Exception as e:
        print(f"\n❌ Error in scrape_cndes_case: {str(e)}")
        logger.error(f"Error in scrape_cndes_case: {str(e)}")
        return {}, False, str(e)

def validate_cndes_data(case_data: Dict) -> bool:
    """
    Validate the scraped case data.
    
    Args:
        case_data (Dict): Scraped case data
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    try:
        # Core required fields that should always be present
        required_fields = [
            'title',
            'disappearance_date',
            'birth_date',
            'age_at_disappearance',
            'current_age',
            'disappearance_location'
        ]
        
        # Check required fields
        missing_fields = [field for field in required_fields if not case_data.get(field)]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            logger.warning(f"Available fields: {list(case_data.keys())}")
            return False
            
        # Additional validation
        if case_data.get('age_at_disappearance') and case_data.get('current_age'):
            if case_data['age_at_disappearance'] > case_data['current_age']:
                logger.warning("Age at disappearance cannot be greater than current age")
                return False
                
        # Log the data we have
        logger.info(f"Successfully validated case data with fields: {list(case_data.keys())}")
        return True
    except Exception as e:
        logger.error(f"Error validating CNDES data: {str(e)}")
        return False 