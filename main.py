import tkinter as tk
from src.gui.main_window import MainWindow
import sys
import traceback

def main():
    root = tk.Tk()
    app = None
    
    try:
        # Set window title and icon
        root.title("Warframe Market Trader")
        
        # Create the application instance
        app = MainWindow(root)
        
        def on_closing():
            if app:
                app.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
    finally:
        # Ensure cleanup happens
        if app:
            try:
                app.destroy()
            except:
                pass
        sys.exit(0)

if __name__ == "__main__":
    main()
