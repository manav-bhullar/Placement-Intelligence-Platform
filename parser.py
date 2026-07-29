import json
import uuid
import os

def parse_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
    
    records = []
    current_record = None
    state = "SEARCHING"
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line == "Back":
            if current_record:
                records.append(current_record)
            current_record = {
                "company_name": "Unknown",
                "role_category": "",
                "question_set_name": "",
                "job_types": [],
                "roles_declaration_type": "",
                "roles": [],
                "eligible_branches": [],
                "questions": [],
                "metadata": {
                    "topics_and_skills": [],
                    "total_questions": 0
                }
            }
            state = "HEADER"
            i += 1
            if i < len(lines):
                current_record["role_category"] = lines[i].strip()
            i += 1
            continue
            
        if not current_record:
            i += 1
            continue
            
        if state == "HEADER":
            if line.startswith("Similar questions asked at "):
                current_record["company_name"] = line.replace("Similar questions asked at ", "").strip()
            elif line.startswith("Question Set"):
                current_record["question_set_name"] = line
            elif line in ["Internship", "Full Time"]:
                if line not in current_record["job_types"]:
                    current_record["job_types"].append(line)
            elif line == "QUESTIONS":
                state = "ROLES_HEADER"
            i += 1
            continue
            
        if state == "ROLES_HEADER":
            if line in ["OFFICIAL ROLES DECLARED BY COMPANY", "ACTUAL ROLES REPORTED BY STUDENTS"]:
                current_record["roles_declaration_type"] = line
                state = "ROLES"
            i += 1
            continue
                
        if state == "ROLES":
            if line == "ELIGIBLE BRANCHES":
                state = "BRANCHES"
            elif line and line not in ["OFFICIAL ROLES DECLARED BY COMPANY", "ACTUAL ROLES REPORTED BY STUDENTS"]:
                current_record["roles"].append(line)
            i += 1
            continue
                
        if state == "BRANCHES":
            if line in ["Technical Questions", "HR Questions", "Additional Practice Questions"]:
                state = "QUESTIONS"
                continue
            elif line == "Topics & Skills":
                state = "TOPICS"
                continue
            elif line:
                current_record["eligible_branches"].append(line)
            i += 1
            continue
                
        if state == "QUESTIONS":
            if line in ["Technical Questions", "HR Questions", "Additional Practice Questions"]:
                q_type = line
                i += 1
                source = lines[i].strip() if i < len(lines) else ""
                i += 1
                count_str = lines[i].strip() if i < len(lines) else "0"
                try:
                    count = int(count_str)
                except ValueError:
                    count = 0
                
                for _ in range(count):
                    i += 1
                    if i >= len(lines): break
                    q_num = lines[i].strip() 
                    i += 1
                    if i >= len(lines): break
                    q_text = lines[i].strip()
                    if q_text:
                        current_record["questions"].append({
                            "question_id": str(uuid.uuid4()),
                            "text": q_text,
                            "type": q_type,
                            "source": source
                        })
                i += 1
                continue
            elif line == "Topics & Skills":
                state = "TOPICS"
                continue
            else:
                i += 1
                continue
                
        if state == "TOPICS":
            if line == "Topics & Skills":
                i += 1 
                if i < len(lines) and lines[i].strip() == "What the company tests":
                    i += 1
                if i < len(lines) and lines[i].strip().isdigit():
                    i += 1
                continue
            elif line == "TietPrep":
                state = "SEARCHING"
            elif line:
                current_record["metadata"]["topics_and_skills"].append(line)
            i += 1
            continue
            
        i += 1

    if current_record:
        records.append(current_record)
        
    for r in records:
        r["metadata"]["total_questions"] = len(r["questions"])
        
    output_path = "tietprep_structured.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully parsed {len(records)} records and saved to {output_path}.")

if __name__ == "__main__":
    parse_data("tietprep raw data")
