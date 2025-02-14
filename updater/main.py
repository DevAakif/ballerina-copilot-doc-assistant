import sys

sys.path.append("C:\\Users\\Aakif_Ahamed\\Projects\\copilot_documentation_assistant_new")
print(sys.path)

from updater import collection_operator
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    collection_operator.update_docs_db()
