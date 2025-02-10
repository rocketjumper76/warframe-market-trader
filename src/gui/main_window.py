import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import queue
import time
from ..api.warframe_market import WarframeMarketAPI
from ..models.item import Item
from ..utils.config import Config
import os


class MainWindow:
    def __init__(self, root):
        # Initialize GUI first for faster perceived loading
        self.root = root
        self.root.title("Warframe Market Trader")
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # Create main container immediately
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create processing queues
        self.analysis_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Setup window and theme
        self.setup_window()
        self.setup_theme()
        
        # Load heavy components in background
        self.root.after(100, self.delayed_init)
    
    def setup_window(self):
        """Setup window size and position"""
        window_width = 800
        window_height = 600
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate center position
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Set window size and position
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.minsize(800, 600)
    
    def setup_theme(self):
        """Setup initial theme"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.is_dark_mode = True
        self._configure_theme()
    
    def _configure_theme(self):
        """Configure the application theme with modern dark colors from the dashboard"""
        if self.is_dark_mode:
            # Dark mode colors from the dashboard
            self.colors = {
                'background': '#1E2128',  # Main dark background
                'secondary': '#262A33',   # Darker panels background
                'text': '#FFFFFF',        # White text
                'accent': '#2CD7C4',      # Turquoise accent
                'accent_dark': '#1FA195', # Darker turquoise
                'graph': '#2B303A',       # Graph background
                'border': '#363B47',      # Border color
                'positive': '#00C853',    # Positive numbers (green)
                'negative': '#FF3D00'     # Negative numbers (red)
            }
        else:
            # Light mode colors (keeping for toggle functionality)
            self.colors = {
                'background': 'SystemButtonFace',
                'secondary': 'SystemWindow',
                'text': 'SystemWindowText',
                'accent': '#2CD7C4',
                'accent_dark': '#1FA195',
                'graph': '#FFFFFF',
                'border': '#E0E0E0',
                'positive': '#00C853',
                'negative': '#FF3D00'
            }

        # Configure styles
        self.style.configure('TFrame', background=self.colors['background'])
        self.style.configure('TLabel', 
                            background=self.colors['background'],
                            foreground=self.colors['text'])
        
        self.style.configure('TLabelframe', 
                            background=self.colors['background'],
                            bordercolor=self.colors['border'])
        
        self.style.configure('TLabelframe.Label', 
                            background=self.colors['background'],
                            foreground=self.colors['text'])
        
        self.style.configure('TButton', 
                            background=self.colors['accent'],
                            foreground=self.colors['text'])
        
        self.style.map('TButton',
                       background=[('active', self.colors['accent_dark'])])
        
        self.style.configure('TEntry', 
                            fieldbackground=self.colors['secondary'],
                            foreground=self.colors['text'],
                            bordercolor=self.colors['border'])
        
        self.style.configure('Treeview', 
                            background=self.colors['secondary'],
                            fieldbackground=self.colors['secondary'],
                            foreground=self.colors['text'],
                            bordercolor=self.colors['border'])
        
        self.style.configure('Treeview.Heading',
                            background=self.colors['background'],
                            foreground=self.colors['text'],
                            bordercolor=self.colors['border'])
        
        self.style.map('Treeview',
                       background=[('selected', self.colors['accent'])],
                       foreground=[('selected', self.colors['text'])])

        # Configure tags for volume coloring
        if hasattr(self, 'tree'):
            self.tree.tag_configure('high_volume', foreground=self.colors['positive'])
            self.tree.tag_configure('low_volume', foreground=self.colors['negative'])
        
        # Update root window
        self.root.configure(bg=self.colors['background'])
    
    def _toggle_theme(self):
        """Toggle between light and dark mode"""
        self.is_dark_mode = not self.is_dark_mode
        self._configure_theme()
    
    def _create_settings_frame(self):
        """Create the settings frame with input fields"""
        settings_frame = ttk.LabelFrame(self.main_container, text="Trading Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create inner frame for content
        content_frame = ttk.Frame(settings_frame)
        content_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Left side - Budget
        budget_frame = ttk.Frame(content_frame)
        budget_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(budget_frame, text="Budget (platinum):").pack(side=tk.LEFT, padx=(0, 5))
        self.budget_var = tk.StringVar(value="100")
        ttk.Entry(budget_frame, textvariable=self.budget_var, width=15).pack(side=tk.LEFT, padx=(0, 20))
        
        # Right side - Buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.X)
        self.analyze_button = ttk.Button(button_frame, text="Start Analysis", command=self._toggle_analysis)
        self.analyze_button.pack(side=tk.LEFT, padx=2)
        self.theme_button = ttk.Button(button_frame, text="Toggle Theme", command=self._toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=2)
    
    def _create_filters_frame(self):
        """Create the filters frame with trading criteria"""
        filters_frame = ttk.LabelFrame(self.main_container, text="Trading Filters")
        filters_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create inner frame for content
        content_frame = ttk.Frame(filters_frame)
        content_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create three equal sections
        for i, (label, var_name, default_value) in enumerate([
            ("Min Profit:", "min_profit_var", str(Config.MIN_PROFIT_MARGIN)),
            ("Min ROI %:", "min_roi_var", str(Config.MIN_ROI_PERCENTAGE)),
            ("Min Daily Volume:", "min_volume_var", str(Config.MIN_DAILY_VOLUME))
        ]):
            frame = ttk.Frame(content_frame)
            frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 5))
            setattr(self, var_name, tk.StringVar(value=default_value))
            ttk.Entry(frame, textvariable=getattr(self, var_name), width=15).pack(side=tk.LEFT)
    
    def _create_results_frame(self):
        """Create the results frame with the trading opportunities table"""
        results_frame = ttk.LabelFrame(self.main_container, text="Trading Opportunities")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create container for treeview and scrollbar
        tree_container = ttk.Frame(results_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ('Item', 'Buy', 'Sell', 'Profit', 'ROI', 'Volume', 'Orders')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings')
        
        # Configure columns with proportional widths
        total_width = 780  # Approximate width
        widths = {
            'Item': int(total_width * 0.25),    # 25%
            'Buy': int(total_width * 0.12),     # 12%
            'Sell': int(total_width * 0.12),    # 12%
            'Profit': int(total_width * 0.12),  # 12%
            'ROI': int(total_width * 0.12),     # 12%
            'Volume': int(total_width * 0.15),  # 15%
            'Orders': int(total_width * 0.12)   # 12%
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], stretch=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags for volume coloring
        self.tree.tag_configure('high_volume', foreground=self.colors['positive'])
        self.tree.tag_configure('low_volume', foreground=self.colors['negative'])
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.main_container, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill=tk.X, padx=5, pady=5)
    
    def _toggle_analysis(self):
        """Toggle market analysis on/off"""
        if not self.analyzing:
            try:
                # Update config with current values
                budget = float(self.budget_var.get())
                if budget <= 0:
                    messagebox.showerror("Invalid Input", "Budget must be greater than 0")
                    return
                    
                Config.MAX_BUDGET = budget  # Update the budget in Config
                
                self.analyzing = True
                self.analyze_button.configure(text="Stop Analysis")
                self._refresh_analysis()
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", "Please enter a valid number for budget")
                return
        else:
            self.analyzing = False
            self.analyze_button.configure(text="Start Analysis")
            self.status_var.set("Analysis stopped")
    
    def _refresh_analysis(self):
        """Refresh market analysis with immediate display"""
        if not self.analyzing:
            return
        
        try:
            self.status_var.set("Refreshing market data...")
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Clear queues
            self.analysis_queue = queue.Queue()
            self.result_queue = queue.Queue()
            
            # First pass: Use cached data for immediate display
            displayed_items = set()
            if hasattr(self.api, 'cache'):
                for cache_key, (orders, _) in self.api.cache.items():
                    if cache_key.startswith('orders_'):
                        item_url = cache_key.replace('orders_', '')
                        if item_url in self.items_cache:
                            item = self.items_cache[item_url]
                            item.orders_cache = orders
                            analysis = item.analyze()
                            if analysis and analysis.is_profitable:
                                self._add_analysis_to_tree(analysis)
                                displayed_items.add(item_url)
            
            # Second pass: Queue remaining items for fresh data
            for url_name, item in self.items_cache.items():
                if url_name not in displayed_items:
                    self.analysis_queue.put(item)
            
            self.status_var.set(f"Analyzing {self.analysis_queue.qsize()} remaining items...")
            
        except Exception as e:
            print(f"Error in refresh_analysis: {str(e)}")
            self.status_var.set("Error refreshing data")
            self.analyzing = False
            self.analyze_button.configure(text="Start Analysis")
    
    def _add_analysis_to_tree(self, analysis):
        """Add analysis results immediately"""
        if analysis and analysis.is_profitable:
            volume_tag = 'high_volume' if analysis.daily_volume >= float(Config.MIN_DAILY_VOLUME) * 2 else 'low_volume'
            self.tree.insert('', 0, values=(
                analysis.name,
                f"{analysis.highest_buy:.1f}",
                f"{analysis.lowest_sell:.1f}",
                f"{analysis.potential_profit:.1f}",
                f"{analysis.roi_percentage:.1f}",
                f"{analysis.daily_volume:.1f}",
                f"{analysis.buy_orders_count}/{analysis.sell_orders_count}"
            ), tags=(volume_tag,))
            self.root.update_idletasks()
    
    def delayed_init(self):
        """Initialize heavy components after GUI is shown"""
        try:
            # Show loading status
            loading_label = ttk.Label(self.main_container, text="Loading items...", font=('Helvetica', 10))
            loading_label.pack(pady=20)
            self.root.update()
            
            # Initialize API and data structures
            self.api = WarframeMarketAPI()
            self.items_cache = {}
            self.analyzing = False
            self.running = True
            
            # Create UI components
            self._create_settings_frame()
            self._create_filters_frame()
            self._create_results_frame()
            self._create_status_bar()
            
            # Start worker threads (4 workers for parallel processing)
            self.workers = []
            for _ in range(4):
                worker = threading.Thread(target=self._analysis_worker, daemon=True)
                worker.start()
                self.workers.append(worker)
            
            # Start result handler thread
            self.result_handler = threading.Thread(target=self._handle_results, daemon=True)
            self.result_handler.start()
            
            # Load items with progress updates
            items_data = self.api.get_items_list()
            total_items = len(items_data)
            
            for i, item_data in enumerate(items_data, 1):
                self.items_cache[item_data['url_name']] = Item(
                    url_name=item_data['url_name'],
                    name=item_data.get('item_name', item_data['url_name']),
                    max_price=Config.MAX_BUDGET
                )
                
                if i % 100 == 0:
                    loading_label.config(text=f"Loading items... ({i}/{total_items})")
                    self.root.update()
            
            loading_label.destroy()
            self.status_var.set("Ready to analyze")
            
        except Exception as e:
            print(f"Error in delayed_init: {str(e)}")
            if 'loading_label' in locals():
                loading_label.destroy()
            self.status_var.set("Error during initialization")
    
    def _analysis_worker(self):
        """Worker thread for processing items"""
        while self.running:
            try:
                if not self.analyzing:
                    time.sleep(1)
                    continue
                
                try:
                    item = self.analysis_queue.get_nowait()
                    
                    # Skip items above budget early
                    if hasattr(item, 'last_buy_price') and item.last_buy_price > Config.MAX_BUDGET:
                        continue
                        
                    item.update_data(self.api)
                    analysis = item.analyze()
                    
                    if analysis:
                        item.last_buy_price = analysis.highest_buy
                        self.result_queue.put(analysis)
                    
                    self.analysis_queue.task_done()
                    
                except queue.Empty:
                    time.sleep(0.1)
                    continue
                
            except Exception as e:
                print(f"Worker error: {str(e)}")
                time.sleep(1)
    
    def _handle_results(self):
        """Handle results from worker threads"""
        batch = []
        last_update = time.time()
        
        while self.running:
            try:
                # Get results without blocking
                try:
                    while len(batch) < 10:  # Max batch size
                        analysis = self.result_queue.get_nowait()
                        if analysis and analysis.is_profitable:
                            batch.append(analysis)
                except queue.Empty:
                    pass
                
                # Update tree if batch is full or enough time has passed
                current_time = time.time()
                if batch and (len(batch) >= 10 or current_time - last_update > 0.1):
                    self.root.after(0, self._update_tree_batch, batch.copy())
                    batch.clear()
                    last_update = current_time
                
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
            except Exception as e:
                print(f"Result handler error: {str(e)}")
                time.sleep(1)
    
    def _update_tree_batch(self, batch):
        """Update tree with a batch of results"""
        for analysis in batch:
            volume_tag = 'high_volume' if analysis.daily_volume >= float(Config.MIN_DAILY_VOLUME) * 2 else 'low_volume'
            self.tree.insert('', 0, values=(
                analysis.name,
                f"{analysis.highest_buy:.1f}",
                f"{analysis.lowest_sell:.1f}",
                f"{analysis.potential_profit:.1f}",
                f"{analysis.roi_percentage:.1f}",
                f"{analysis.daily_volume:.1f}",
                f"{analysis.buy_orders_count}/{analysis.sell_orders_count}"
            ), tags=(volume_tag,))
        
        self.root.update_idletasks()
    
    def destroy(self):
        """Clean up resources"""
        self.running = False
        self.analyzing = False
        
        # Clean up threads
        if hasattr(self, 'result_handler') and self.result_handler.is_alive():
            self.result_handler.join(timeout=1.0)
        
        # Clean up API
        if hasattr(self, 'api'):
            self.api.cleanup()
        
        # Clean up window
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.quit()
            self.root.destroy()