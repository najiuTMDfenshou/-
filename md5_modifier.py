import os
import hashlib
import random
import shutil  # 添加这行导入
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import webbrowser

class MD5Modifier:
    """MD5批量修改工具主类
    
    功能包含：
    - 文件选择与管理
    - MD5值计算与修改
    - 处理状态跟踪
    - 结果输出
    """
    def __init__(self, master):
        self.master = master
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        self.master.title("MD5批量修改工具")
        self.create_treeview()
        self.create_toolbar()
        self.create_preview()
        self.create_context_menu()
        self.create_github_link()  # 新增方法调用

    def create_github_link(self):
        # 创建超链接标签
        link = tk.Label(self.master, text="作者Github", fg="blue", cursor="hand2")
        link.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/najiuTMDfenshou"))

    def create_context_menu(self):
        # 创建右键菜单
        self.context_menu = tk.Menu(self.master, tearoff=0)
        menu_items = [
            ("替换文件", self.replace_file),
            ("全选文件", self.select_all),
            ("删除文件", self.delete_selected),
            ("取消选择", self.clear_selection),
            ("反向选择", self.invert_selection)
        ]
        for text, cmd in menu_items:
            self.context_menu.add_command(label=text, command=cmd)
        
        # 绑定右键事件
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        # 在点击位置显示菜单
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # 右键功能实现
    def replace_file(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要替换的文件")
            return
            
        new_files = filedialog.askopenfilenames()
        if not new_files:
            return
        
        # 批量替换逻辑
        for i, item in enumerate(selected_items):
            if i < len(new_files):  # 替换现有条目
                new_path = new_files[i]
                if os.path.isfile(new_path):
                    self.tree.item(item, values=(
                        new_path,
                        self.calculate_md5(new_path),
                        "",
                        "待处理",
                        f"{os.path.getsize(new_path)/1024:.1f}KB"
                    ))
            else:  # 删除多余条目
                self.tree.delete(item)
        
        # 添加额外的新文件
        if len(new_files) > len(selected_items):
            for path in new_files[len(selected_items):]:
                if not self.exists_in_tree(path):
                    self.add_file(path)

    def select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def delete_selected(self):
        for item in self.tree.selection():
            self.tree.delete(item)

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())

    def invert_selection(self):
        all_items = set(self.tree.get_children())
        selected = set(self.tree.selection())
        self.tree.selection_set(*all_items - selected)

    def create_treeview(self):
        self.tree = ttk.Treeview(self.master, columns=("path", "original", "new", "status", "size"), 
                               show="headings", height=15)
        columns = [
            ("path", "文件路径", 300),
            ("original", "初始MD5", 120),
            ("new", "新MD5", 120),
            ("status", "状态", 80),
            ("size", "大小", 80)  # 新增大小列
        ]
        for col_id, text, width in columns:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def clear_list(self):  # 将此方法移到create_toolbar之前
        for item in self.tree.get_children():
            self.tree.delete(item)

    def create_toolbar(self):
        toolbar = tk.Frame(self.master)
        buttons = [
            ("选择文件", self.select_files),
            ("选择文件夹", self.select_folder),
            ("处理文件", self.process_files),
            ("清空列表", self.clear_list)
            # 已移除打开目标按钮
        ]
        for text, cmd in buttons:
            tk.Button(toolbar, text=text, command=cmd).pack(side=tk.LEFT, padx=2)
        toolbar.pack(pady=5)

    def create_preview(self):
        self.preview = tk.Text(self.master, height=4, state=tk.DISABLED)
        self.preview.pack(fill=tk.X)

    def show_preview(self, event):
        item = self.tree.selection()[0]
        path = self.tree.item(item)["values"][0]
        info = f"文件路径: {path}\nMD5: {self.tree.item(item)['values'][1]}"
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, info)
        self.preview.config(state=tk.DISABLED)

    def toggle_status(self, event):
        item = self.tree.identify_row(event.y)
        current = self.tree.item(item)["values"][3]
        new_status = "已处理" if current == "待处理" else "待处理"
        self.tree.set(item, "status", new_status)

    def setup_bindings(self):
        self.tree.bind("<<TreeviewSelect>>", self.show_preview)
        self.tree.bind("<Double-1>", self.toggle_status)

    # 核心功能实现
    def select_files(self):
        try:
            files = filedialog.askopenfilenames()
            if files:
                added_count = 0  # 新增计数器
                for path in files:
                    if not self.exists_in_tree(path):
                        self.add_file(path)
                        added_count += 1
                
                # 添加结果提示
                if added_count == 0:
                    messagebox.showinfo("提示", "未发现新文件")
                else:
                    messagebox.showinfo("完成", f"成功添加 {added_count} 个文件")
        except Exception as e:
            messagebox.showerror("错误", f"文件选择失败: {str(e)}")

    def select_folder(self):
        try:
            folder = filedialog.askdirectory()
            if folder: 
                existing_files = {self.tree.item(i)["values"][0] for i in self.tree.get_children()}
                added_count = 0
                
                # 修复：仅处理当前目录文件（不遍历子目录）
                for entry in os.listdir(folder):
                    path = os.path.join(folder, entry)
                    if os.path.isfile(path) and path not in existing_files:
                        self.add_file(path)
                        added_count += 1
                
                if added_count == 0:
                    messagebox.showinfo("提示", "未发现新文件")
                else:
                    messagebox.showinfo("完成", f"成功添加 {added_count} 个文件")
        except Exception as e:
            messagebox.showerror("错误", f"目录选择失败: {str(e)}")

    def open_target_folder(self):
        try:
            if hasattr(self, 'target_dir') and os.path.isdir(self.target_dir):
                os.startfile(self.target_dir)  # Windows系统打开文件夹
            else:
                messagebox.showwarning("提示", "尚未生成目标文件夹")
        except Exception as e:
            messagebox.showerror("错误", f"打开失败：{str(e)}")

    def process_files(self):
        src_dir = self.get_source_directory()
        if not src_dir:
            return
        
        # 新增路径选择对话框
        use_default = messagebox.askyesno("路径选择", "是否使用默认保存路径？\n(否则将弹出目录选择框)")
        if use_default:
            target_dir = self.create_default_dir(src_dir)
        else:
            target_dir = filedialog.askdirectory(initialdir=src_dir)
        
        if not target_dir:
            return
        
        # 处理文件逻辑保持不变
        for item in self.tree.get_children():
            path = self.tree.item(item)["values"][0]
            if self.tree.item(item)["values"][3] == "待处理":
                new_path = self.process_single_file(path, target_dir)
                self.update_item_status(item, new_path)

    def get_source_directory(self):
        """获取首个文件的原始目录"""
        if items := self.tree.get_children():
            first_file = self.tree.item(items[0])["values"][0]
            return os.path.dirname(first_file)
        return None

    def create_default_dir(self, src_dir):
        """创建默认保存目录"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        dir_name = f"{date_str}-修改md5值"
        target_dir = os.path.join(src_dir, dir_name)
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            return target_dir
        except Exception as e:
            messagebox.showerror("错误", f"创建目录失败：{str(e)}")
            return None

    def process_single_file(self, src, target_dir):
        """修改后的文件处理逻辑"""
        try:
            if not os.path.exists(src):
                raise FileNotFoundError(f"原始文件不存在：{src}")
                
            file_name = os.path.basename(src)
            dst = os.path.join(target_dir, file_name)
            
            # 复制文件而不是直接修改原始文件
            shutil.copy2(src, dst)
            
            # 追加随机字节
            with open(dst, "ab") as f:
                f.write(bytes([random.randint(0,255) for _ in range(4)]))
                
            return dst
        except Exception as e:
            messagebox.showerror("错误", f"处理文件失败：{str(e)}")
            return None

    # 辅助方法
    def get_output_dir(self):
        default = os.path.join(os.path.expanduser("~"), "MD5_Modified")
        return filedialog.askdirectory(initialdir=default) or default

    def exists_in_tree(self, path):
        return any(self.tree.item(i)["values"][0] == path 
                 for i in self.tree.get_children())

    def calculate_md5(self, path):
        hasher = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def add_file(self, path):
        file_size = f"{os.path.getsize(path)/1024:.1f}KB"
        values = (
            path,
            self.calculate_md5(path),
            "",
            "待处理",
            file_size
        )
        self.tree.insert("", tk.END, values=values)

    def update_item_status(self, item, new_path):
        if not new_path or not os.path.exists(new_path):  # 添加文件存在性检查
            messagebox.showerror("错误", "生成文件路径无效")
            return

        try:
            new_md5 = self.calculate_md5(new_path)
            new_size = f"{os.path.getsize(new_path)/1024:.1f}KB"
            
            self.tree.item(item, values=(
                new_path,
                self.tree.item(item)["values"][1],
                new_md5,
                "已完成",
                new_size
            ))
        except Exception as e:
            messagebox.showerror("更新错误", f"无法更新条目状态：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MD5Modifier(root)
    root.mainloop()