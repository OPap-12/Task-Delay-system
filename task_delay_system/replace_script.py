import os

def replace_due_date(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for name in files:
            if name.endswith(('.py', '.html', '.js', '.css')):
                filepath = os.path.join(root, name)
                if 'replace_script.py' in filepath:
                    continue
                    
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'due_date' in content:
                    content = content.replace('due_date', 'deadline')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {filepath}")

if __name__ == "__main__":
    replace_due_date('.')
