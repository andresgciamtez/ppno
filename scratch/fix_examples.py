import os

def fix_file(path, search_text, replace_text):
    try:
        # Try different encodings
        for enc in ['utf-8', 'cp1252', 'latin-1']:
            try:
                with open(path, 'r', encoding=enc) as f:
                    content = f.read()
                print(f"Successfully read {path} with {enc}")
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Could not read {path} with any common encoding")
            return

        if search_text in content:
            new_content = content.replace(search_text, replace_text)
            with open(path, 'w', encoding=enc) as f:
                f.write(new_content)
            print(f"Successfully updated {path}")
        else:
            print(f"Search text not found in {path}")
    except Exception as e:
        print(f"Error processing {path}: {e}")

examples_dir = 'ppno/examples'
new_comment = '; Available: UH, DE, DA, SHGO, DIRECT, NSGA2, MOEAD, MACO, PSO'

# Fix Example 5
fix_file(os.path.join(examples_dir, 'Example5.ext'), 
         'Algorithm UH ; UH (Unit Headloss Heuristic), DE (Differential Evolution) or DA (Dual Annealing)',
         f'Algorithm UH {new_comment}')

# Fix Example 6
fix_file(os.path.join(examples_dir, 'Example6.ext'), 
         'Algorithm NSGA2',
         f'Algorithm NSGA2 {new_comment}')
