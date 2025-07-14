import argparse
import os
import random
import re
from pathlib import Path
from encodings_list import all_encodings

def parse_hl7_message(hl7_message):
    # Define field mappings for common segments
    field_mappings = {
        "MSH": {
            1:  "Field Separator", # |
            2:  "Encoding Characters", # ^~\&
            3:  "Sending Application", # ALTERIS/Zew Sys
            4:  "Sending Facility", # ALTERIS/Zew Sys
            5:  "Receiving Application", # Zew sys/ALTERIS
            6:  "Receiving Facility", # Zew sys/ALTERIS
            7:  "Date/Time of Message", # 20090729141016700
            8:  "Security", #
            9:  "Message Type", # ORM^O01
            10: "Message Control ID", # 139658
            11: "Processing ID", # P : Proces produkcyjny (P) / Proces treningowy (T)
            12: "Version ID", # 2.3
            13: "Sequence ID", #
            14: "Continuation Pointer", #
            15: "Accept Acknowledgement Type", #
            16: "Application Acknowledgement Type", #
            17: "Country Code", # POL
            18: "Character Set", # CP1250
            19: "Principal Language of Message", # PL
        },
        "PID": {
            1:  "Set ID - Patient ID", #
            2:  "Patient ID (External ID)", # 27101205534 lub 123243^^^^PPS
            3:  "Patient ID (Internal ID)", # 158482
            4:  "Alternate Patient ID", #
            5:  "Patient Name", # KLOSIŃSKI^MARIUSZ
            6:  "Mother’s Maiden Name", #
            7:  "Date/Time of Birth", # 19271012
            8:  "Administrative Sex", # M
            9:  "Patient Alias", #
            10: "Race", #
            11: "Patient Address", # Opolska^123/12a&amp;9^Katowice^^40-057
            12: "County Code", #
            13: "Phone Number - Home", #
            14: "Phone Number - Business", #
            15: "Primary Language", #
            16: "Marital Status", #
            17: "Religion", #
            18: "Patient Account Number", #
            19: "SSN Number - Patient", #
            20: "Driver’s Lic Num – Patient", #
            21: "Mother’s Identifier", #
            22: "Ethnic Group", #
            23: "Birth Place", #
            24: "Multiple Birth Indicator", #
            25: "Birth Order", #
            26: "Citizenship", #
            27: "Veterans Military Status", #
            28: "Nationality", #
            29: "Patient Death Date/Time", #
            30: "Patient Death Indicator", #
        },
        "IN1": {
            1:  "Set ID", #
            2:  "Insurance Plan ID", #
            3:  "Insurance Company ID", #
            4:  "Insurance Company Name"
        },
        "ORC": {
            1:  "Order Control", # NW : NW – nowe zlecenia; XO – aktualizacja zlecena; CA – anulowanie badania; RE – w przypadku komunikatu ORU zawierającego wynik
            2:  "Place Order Number", # 1234567
            3:  "Filler Order Number", #
            4:  "Placer Group Number", #
            5:  "Order Status", #
            6:  "Response Flag", #
            7:  "Quantity/Timing", #
            8:  "Parent", #
            9:  "Date/Time of Transaction", # 20090813125155
            10: "Entered By", #
            11: "Verified By", #
            12: "Ordering Provider", # NPWZ
            13: "Enterer’s Location",
            14: "Call Back Phone Number", #
            15: "Order Effective Date/Time", #
            16: "Order Control Reason", #
            17: "Entering Organization", # REGON
            18: "Entering Device", #
            19: "Action By" #
        },
        "OBR": { # Observation Request
            1:  "Set ID - Observation Request", #
            2:  "Placer Order Number", # 1234567 order ID in HIS
            3:  "Filler Order Number", # # order ID in RIS
            4:  "Universal Service ID", # 2567^CT głowy&574 Id usługi^nazwa^kod usługi
            5:  "Priority", #
            6:  "Requested Date/Time", #
            7:  "Observation Date/Time", #
            8:  "Observation End Date/Time", #
            9:  "Collection Volume", #
            10: "Collector Identifier", #
            11: "Specimen Action Code", #
            12: "Danger Code", #
            13: "Relevant Clinical Inf.", # Kod ICD10
            14: "Specimen Rec'd Date/Time", #
            15: "Specimen Source", #
            16: "Ordering Provider family", # NPWZ
            17: "Order Callback Phone No.", #
            18: "Placer Field 1", #
            19: "Placer Field 2", #
            20: "Filler Field 1", #
            21: "Filler Field 2", #
            22: "Result Rpt/Status Change - Date/Time", #
            23: "Charge To Practice", #
            24: "Diagnostic Serv Sect Id", #
            25: "Result Status", #
            26: "Parent Result", #
            27: "Quantity/Timing", #
            28: "Result Copies To", #
            29: "Parent Number", #
            30: "Transportation Mode", #
            31: "Reason For Study", #
            32: "Principal Result Interpreter", #
            33: "Assistant Result Interpreter", #
            34: "Technician", #
            35: "Transcriptionist", #
            36: "Scheduled Date/Time", #
            37: "Number of Sample Containers", #
            38: "Transport Logistics of Collected Sample", #
            39: "Collector's Comment", #
            40: "Transport Arrangement Responsibility", #
            41: "Transport Arranged", #
            42: "Escort Required", #
            43: "Planned Patient Transport Comment"
        },
        "NTE": {
            1:  "Set ID – NTE", #
            2:  "Source of Comment", #
            3:  "Comment" #
        },
        "OBX": {
            1:  "Set ID - OBX", #
            2:  "Value Type", # FT : FT - Treść opisu; ED - załącznik do wyniku
            3:  "Observation Identifier", # 123/TK/09 : Dicom Accession Number
            4:  "Observation Sub-ID", # : 192.168.4.150/Ris/future.php?action=choseTemplate&amp;EID=221235^192.168.4.150/Ris/imgview.php?AccNum=12711/16/2011
            5:  "Observation Value", # Dokument&2^wynik_123232.pdf^PDF^Base64^yGTRVVGew2rcRTASC==
            6:  "Units", #
            7:  "Reference Range", #
            8:  "Abnormal Flags", #
            9:  "Probability", #
            10: "Nature of Abnormal Test", #
            11: "Observation Result Status", #
            12: "Date Last Obs Normal Values", #
            13: "User Defined Access Checks", #
            14: "Date/Time of the Observation", # 20090729125924
            15: "Producer’s ID", #
            16: "Responsible Observer", # NPWZ
            17: "Observation Method", # 9.12^5.03.00.0000075 : ICD ^ kod świadczenia NFZ
            32: "Interpretation Author", #
            35: "Interpretation Transcriber" #
        },
        "PV1": {
            1:  "Set ID - PV1", #
            2:  "Patient Class", #
            3:  "Assigned Patient Location", #
            10: "Hospital Service", #
            17: "Admitting Doctor", #
            19: "Visit Number", #
        },
        "PV2": {
            4:  "Transfer Reason", #
            8:  "Expected Admit Date", #
            24: "Patient Status Code", #
            25: "Visit Priority Code" #
        },
        "EVN": {
            1: "Event Type Code", #
            2: "Recorded Date/Time", #
            3: "Date/Time Planned Event", #
            4: "Event Reason Code", #
            5: "Operator ID", #
            6: "Event Occurred" #
        },
        "MRG": {
            1:  "Prior Patient ID - Internal", # 11136_ ExtID – identyfikator pacjenta który ma zostać dołączony do właściwego i usunięty
            2:  "Prior Alternate Patient ID", #
            3:  "Prior Patient Account Number", #
            4:  "Prior Patient ID - External", #
            5:  "Prior Visit Number", #
            6:  "Prior Alternate Visit ID", #
            7:  "Prior Patient Name" #
        },
        "MFI": {
            1:  "Master File Identifier", # : BAD – słownik badań ; USR – słownik użytkowników ; MAT – słownik materiałów
            2:  "Master File Application Identifier", #
            3:  "File-Level Event Code", # UPD – aktualizacja danych ; REP – zastąpienie danych
            4:  "Entered Date/Time", #
            5:  "Effective Date/Time", #
            6:  "Response Level Code" #
        },
        "MFE": {
            1:  "Record-Level Event Code", # : MAD - dodanie rekordu ; MUP - aktualizacja rekordu ; MDC - deaktywacja rekordu
            2:  "MFN Control ID", #
            3:  "Effective Date/Time", #
            4:  "Primary Key Value" #
        },
        "ZMF": {
            1:  "", # Identyfikator w systemie
            2:  "", # Wartość słownikowa : Np.: kod badania
            3:  "", # Wartość słownikowa : Np.: nazwa badania
            4:  ""  # Wartość słownikowa : Np.: nazwa badania
        }
    }

    # HL7 segments are typically separated by \r (carriage return)
    segments = hl7_message.strip().split('\n')

    print() # separate info about file and encoding from segments of a file

    # Parse each segment
    for segment in segments:
        fields = segment.split('|')
        segment_type = fields[0]
        print(f"Segment: {segment_type}")

        # Get field mapping for the segment if exists
        mapping = field_mappings.get(segment_type, {})

        start_index = 1

        # Print each field with its name if known
        for i in range(start_index, len(fields)):
            field_num = i  # HL7 fields are 1-indexed, fields[1] is field #1
            field_value = fields[i]
            if field_value:
                field_name = mapping.get(field_num, f"Field #{field_num}")
                # Add a space after single-digit field_num for alignment, no space after two-digit
                space = " " if field_num < 10 else ""
                print(f"  \033[90m{space}{field_num}\033[0m: \033[90m{field_name}\033[0m: \033[97m{field_value}\033[0m")

        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='HL7 Parser',
        description='Pass a file as an argument to parse it',
        epilog='python parser.py <your_file.hl7>')

    parser.add_argument(
        'file',
        nargs='?',
        type=str,
        help='HL7 file(s) to be parsed'
    )

    args = parser.parse_args()

    if args.file:
        file = Path(args.file)
    else:
        path_to_hl7 = Path("./hl7")
        file = random.choice([f for f in path_to_hl7.iterdir() if f.is_file()])

    print(file)

    with file.open("r") as f:
        raw_data = f.readline()

    all_encodings = all_encodings()

    encoding_in_file = "CP1250"

    for enc in all_encodings:
        try:
            enc_upper = enc.upper()
            if enc_upper in raw_data:
                found_encoding = True
                encoding_in_file = enc_upper
                print(f"[!] FOUND - {encoding_in_file}")
                break

        except (UnicodeDecodeError, LookupError):
            continue

    with open(file, "r", encoding='utf-8') as f:
        hl7_message = f.read()

    parse_hl7_message(hl7_message)
