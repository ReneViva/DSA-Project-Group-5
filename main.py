# main.py
import os

if __name__ == "__main__":
    # Ensure we are in the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Launch Streamlit app
    os.system("streamlit run src/ui/app.py")

