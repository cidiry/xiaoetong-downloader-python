# -*- coding: utf-8 -*-
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app_config import build_config_from_cookie_string, has_valid_config, load_config, save_config
from link_service import (
    export_links_to_txt,
    extract_links_for_resources,
    format_link_results,
    list_course_nodes,
    list_course_resources,
    list_purchased_courses,
)


class XiaoETongApp:
    def __init__(self, root):
        self.root = root
        self.root.title('小鹅通下载链接提取工具')
        self.root.geometry('1200x720')

        self.message_queue = queue.Queue()
        self.busy = False
        self.purchased_courses = []
        self.course_nodes = []
        self.course_resources = []
        self.latest_result = None
        self.export_dir = str(Path.cwd() / 'url')
        self.cookie_text = None
        self.saved_config = load_config()

        self.status_var = tk.StringVar(value='准备就绪')
        self.progress_var = tk.IntVar(value=0)
        self.max_workers_var = tk.IntVar(value=3)
        self.delay_seconds_var = tk.DoubleVar(value=0.0)

        self._build_ui()
        self._load_saved_cookie_config()
        self.root.after(100, self._process_queue)

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        config_frame = ttk.LabelFrame(top_frame, text='Cookies 配置', padding=8)
        config_frame.pack(fill=tk.X)
        config_frame.columnconfigure(0, weight=1)

        self.cookie_text = tk.Text(config_frame, height=5, wrap=tk.WORD)
        self.cookie_text.grid(row=0, column=0, columnspan=2, sticky='ew')

        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=(8, 0))

        self.save_cookie_button = ttk.Button(button_frame, text='保存 Cookies', command=self.save_cookie_config)
        self.save_cookie_button.pack(side=tk.LEFT)

        self.load_button = ttk.Button(button_frame, text='加载已购课程', command=self.load_purchased_courses)
        self.load_button.pack(side=tk.LEFT, padx=(8, 0))

        main_frame = ttk.Frame(self.root, padding=(10, 0, 10, 0))
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.purchased_listbox = self._build_list_panel(main_frame, 0, '已购课程')
        self.purchased_listbox.bind('<<ListboxSelect>>', self.on_purchased_selected)

        self.node_listbox = self._build_list_panel(main_frame, 1, '子课程')
        self.node_listbox.bind('<<ListboxSelect>>', self.on_node_selected)

        resource_frame = ttk.Frame(main_frame)
        resource_frame.grid(row=0, column=2, sticky='nsew', padx=(8, 0))
        resource_frame.rowconfigure(2, weight=1)
        resource_frame.columnconfigure(0, weight=1)

        ttk.Label(resource_frame, text='视频/直播').grid(row=0, column=0, sticky='w')
        ttk.Label(resource_frame, text='可按 Ctrl/Shift 多选 Ctrl+A全选').grid(row=1, column=0, sticky='w', pady=(2, 6))

        list_frame = ttk.Frame(resource_frame)
        list_frame.grid(row=2, column=0, sticky='nsew')
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.resource_listbox = tk.Listbox(list_frame, exportselection=False, selectmode=tk.EXTENDED)
        self.resource_listbox.grid(row=0, column=0, sticky='nsew')
        resource_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.resource_listbox.yview)
        resource_scrollbar.grid(row=0, column=1, sticky='ns')
        self.resource_listbox.configure(yscrollcommand=resource_scrollbar.set)

        settings_frame = ttk.LabelFrame(resource_frame, text='获取链接设置', padding=8)
        settings_frame.grid(row=3, column=0, sticky='ew', pady=(8, 0))
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)

        ttk.Label(settings_frame, text='线程数').grid(row=0, column=0, sticky='w')
        self.max_workers_spinbox = tk.Spinbox(
            settings_frame,
            from_=1,
            to=20,
            increment=1,
            width=6,
            textvariable=self.max_workers_var,
        )
        self.max_workers_spinbox.grid(row=0, column=1, sticky='w', padx=(8, 16))

        ttk.Label(settings_frame, text='延迟(s)').grid(row=0, column=2, sticky='w')
        self.delay_spinbox = tk.Spinbox(
            settings_frame,
            from_=0.0,
            to=5.0,
            increment=0.1,
            width=6,
            format='%.1f',
            textvariable=self.delay_seconds_var,
        )
        self.delay_spinbox.grid(row=0, column=3, sticky='w', padx=(8, 0))

        ttk.Label(settings_frame, text='线程越少越安全，越不容易报错').grid(row=1, column=0, columnspan=4, sticky='w', pady=(6, 0))

        action_frame = ttk.Frame(resource_frame)
        action_frame.grid(row=4, column=0, sticky='ew', pady=(8, 0))
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        self.fetch_button = ttk.Button(action_frame, text='获取所选视频/直播链接', command=self.fetch_selected_links)
        self.fetch_button.grid(row=0, column=0, sticky='ew')

        self.export_button = ttk.Button(action_frame, text='导出 txt', command=self.export_current_result, state=tk.DISABLED)
        self.export_button.grid(row=0, column=1, sticky='ew', padx=(8, 0))

        progress_frame = ttk.Frame(self.root, padding=10)
        progress_frame.pack(fill=tk.X)

        self.progressbar = ttk.Progressbar(progress_frame, maximum=100, variable=self.progress_var)
        self.progressbar.pack(fill=tk.X)

        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(6, 0))

        result_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        result_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(result_frame, text='链接结果').pack(anchor=tk.W)
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, height=16)
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.result_text.configure(yscrollcommand=scrollbar.set)

    def _build_list_panel(self, parent, column, title, selectmode=tk.BROWSE):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky='nsew', padx=(0 if column == 0 else 8, 0))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=title).grid(row=0, column=0, sticky='w', pady=(0, 6))
        listbox = tk.Listbox(frame, exportselection=False, selectmode=selectmode)
        listbox.grid(row=1, column=0, sticky='nsew')

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        listbox.configure(yscrollcommand=scrollbar.set)
        return listbox

    def set_busy(self, busy, status_text=None):
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.load_button.configure(state=state)
        self.fetch_button.configure(state=state)
        if hasattr(self, 'save_cookie_button'):
            self.save_cookie_button.configure(state=state)
        if hasattr(self, 'max_workers_spinbox'):
            self.max_workers_spinbox.configure(state=state)
        if hasattr(self, 'delay_spinbox'):
            self.delay_spinbox.configure(state=state)
        if hasattr(self, 'export_button'):
            export_state = tk.DISABLED if busy or not self.latest_result else tk.NORMAL
            self.export_button.configure(state=export_state)
        if status_text:
            self.status_var.set(status_text)

    def load_purchased_courses(self):
        if self.busy:
            return
        if not has_valid_config():
            messagebox.showwarning('提示', '请先填写并保存 cookies 配置。')
            return
        self._start_worker(self._load_purchased_courses_worker, '正在加载已购课程...')

    def on_purchased_selected(self, _event=None):
        if self.busy:
            return
        selection = self.purchased_listbox.curselection()
        if not selection:
            return
        purchased = self.purchased_courses[selection[0]]
        self._start_worker(
            self._load_course_nodes_worker,
            f"正在加载《{purchased['name']}》的子课程...",
            purchased,
        )

    def on_node_selected(self, _event=None):
        if self.busy:
            return
        selection = self.node_listbox.curselection()
        if not selection:
            return
        node = self.course_nodes[selection[0]]
        self._start_worker(
            self._load_resources_worker,
            f"正在加载《{node['name']}》的视频列表...",
            node,
        )

    def fetch_selected_links(self):
        if self.busy:
            return
        node_selection = self.node_listbox.curselection()
        if not node_selection:
            messagebox.showwarning('提示', '请先选择一个子课程。')
            return
        if not self.course_resources:
            messagebox.showwarning('提示', '当前子课程还没有可处理的视频或直播资源。')
            return
        try:
            self._normalize_fetch_settings()
        except ValueError as exc:
            messagebox.showwarning('提示', str(exc))
            return

        node = self.course_nodes[node_selection[0]]
        resource_indices = self.resource_listbox.curselection()
        if resource_indices:
            resources = [self.course_resources[index] for index in resource_indices]
        else:
            resources = list(self.course_resources)
            self.status_var.set('未单独选择视频，默认处理当前子课程全部资源')

        self.latest_result = None
        self.export_button.configure(state=tk.DISABLED)
        self.result_text.delete('1.0', tk.END)
        self.progress_var.set(0)
        self.progressbar.configure(maximum=max(len(resources), 1))
        self._start_worker(
            self._fetch_links_worker,
            f"正在获取《{node['name']}》的下载链接...",
            node,
            resources,
        )

    def _start_worker(self, target, status_text, *args):
        self.set_busy(True, status_text)
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def _normalize_fetch_settings(self):
        try:
            max_workers = int(self.max_workers_var.get())
        except (tk.TclError, ValueError) as exc:
            raise ValueError('线程数必须是 1 到 20 之间的整数') from exc
        try:
            delay_seconds = round(float(self.delay_seconds_var.get()), 1)
        except (tk.TclError, ValueError) as exc:
            raise ValueError('延迟时间必须是 0.0 到 5.0 之间的数字') from exc

        if not 1 <= max_workers <= 20:
            raise ValueError('线程数必须是 1 到 20 之间的整数')
        if not 0.0 <= delay_seconds <= 5.0:
            raise ValueError('延迟时间必须是 0.0 到 5.0 之间的数字')

        self.max_workers_var.set(max_workers)
        self.delay_seconds_var.set(delay_seconds)
        return max_workers, delay_seconds

    def _load_purchased_courses_worker(self):
        try:
            items = list_purchased_courses()
            self.message_queue.put(('set_purchased', items))
            self.message_queue.put(('status', f'已加载 {len(items)} 个已购课程'))
        except Exception as exc:
            self.message_queue.put(('error', f'加载已购课程失败：{exc}'))
        finally:
            self.message_queue.put(('done', None))

    def _load_course_nodes_worker(self, purchased):
        try:
            items = list_course_nodes(purchased['product_id'])
            self.message_queue.put(('set_nodes', items))
            self.message_queue.put(('clear_resources', None))
            self.message_queue.put(('status', f"《{purchased['name']}》共加载 {len(items)} 个子课程"))
        except Exception as exc:
            self.message_queue.put(('error', f'加载子课程失败：{exc}'))
        finally:
            self.message_queue.put(('done', None))

    def _load_resources_worker(self, node):
        try:
            items = [
                item
                for item in list_course_resources(node['course_id'], product_id=node.get('product_id'))
                if item['supported']
            ]
            self.message_queue.put(('set_resources', items))
            self.message_queue.put(('status', f"《{node['name']}》共加载 {len(items)} 个可处理资源"))
        except Exception as exc:
            self.message_queue.put(('error', f'加载资源失败：{exc}'))
        finally:
            self.message_queue.put(('done', None))

    def _fetch_links_worker(self, node, resources):
        try:
            max_workers, delay_seconds = self._normalize_fetch_settings()
            result = extract_links_for_resources(
                node['course_id'],
                node['name'],
                resources,
                progress_callback=self._queue_progress,
                status_callback=self._queue_status,
                log_callback=self._queue_log,
                product_id=node.get('product_id'),
                max_workers=max_workers,
                delay_seconds=delay_seconds,
            )
            self.message_queue.put(('structured_result', result))
            self.message_queue.put(('result', format_link_results(result)))
            self.message_queue.put(('status', f"处理完成：成功 {result['success']}，失败 {result['failed']}"))
        except Exception as exc:
            self.message_queue.put(('error', f'获取下载链接失败：{exc}'))
        finally:
            self.message_queue.put(('done', None))

    def _queue_progress(self, current, total, title):
        self.message_queue.put(('progress', (current, total, title)))

    def _queue_status(self, text):
        self.message_queue.put(('status', text))

    def _queue_log(self, text):
        self.message_queue.put(('append_result', text))

    def _process_queue(self):
        while True:
            try:
                event, payload = self.message_queue.get_nowait()
            except queue.Empty:
                break

            if event == 'set_purchased':
                self.purchased_courses = payload
                self._fill_listbox(self.purchased_listbox, [item['name'] for item in payload])
                self._fill_listbox(self.node_listbox, [])
                self._fill_listbox(self.resource_listbox, [])
                self.course_nodes = []
                self.course_resources = []
            elif event == 'set_nodes':
                self.course_nodes = payload
                self._fill_listbox(self.node_listbox, [item['name'] for item in payload])
            elif event == 'set_resources':
                self.course_resources = payload
                labels = [f"[{item['resource_type_label']}] {item['title']}" for item in payload]
                self._fill_listbox(self.resource_listbox, labels)
            elif event == 'clear_resources':
                self.course_resources = []
                self._fill_listbox(self.resource_listbox, [])
            elif event == 'progress':
                current, total, title = payload
                self.progressbar.configure(maximum=max(total, 1))
                self.progress_var.set(current)
                self.status_var.set(f'正在获取下载链接：{current}/{total} - {title}')
            elif event == 'status':
                self.status_var.set(payload)
            elif event == 'structured_result':
                self.latest_result = payload
                if not self.busy:
                    self.export_button.configure(state=tk.NORMAL)
            elif event == 'result':
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert(tk.END, payload)
                if self.latest_result:
                    self.export_button.configure(state=tk.NORMAL)
            elif event == 'append_result':
                if self.result_text.get('1.0', tk.END).strip():
                    self.result_text.insert(tk.END, f'\n{payload}\n')
                else:
                    self.result_text.insert(tk.END, f'{payload}\n')
                self.result_text.see(tk.END)
            elif event == 'error':
                self.status_var.set(payload)
                messagebox.showerror('错误', payload)
            elif event == 'done':
                self.set_busy(False)

        self.root.after(100, self._process_queue)

    def save_cookie_config(self):
        if self.busy:
            return
        cookie_string = self.cookie_text.get('1.0', tk.END).strip()
        if not cookie_string:
            messagebox.showwarning('提示', '请输入 cookies 字符串。')
            return
        try:
            config = build_config_from_cookie_string(cookie_string)
            self.saved_config = save_config(config)
            self.status_var.set('Cookies 配置已保存，下次启动会自动加载')
            messagebox.showinfo('保存成功', 'Cookies 配置已保存。')
        except Exception as exc:
            messagebox.showerror('保存失败', f'保存 cookies 失败：{exc}')

    def _load_saved_cookie_config(self):
        cookie_string = self.saved_config.get('cookie_string', '')
        if cookie_string:
            self.cookie_text.delete('1.0', tk.END)
            self.cookie_text.insert(tk.END, cookie_string)
            self.status_var.set('已加载本地保存的 cookies 配置')
        else:
            self.status_var.set('请先粘贴并保存 cookies 配置')
            self.root.after(200, lambda: messagebox.showinfo('提示', '首次使用请先填写并保存 cookies 配置。'))

    def export_current_result(self):
        if not self.latest_result:
            messagebox.showwarning('提示', '请先获取下载链接后再导出。')
            return
        output_dir = filedialog.askdirectory(initialdir=self.export_dir, title='选择导出目录')
        if not output_dir:
            return
        try:
            file_path = export_links_to_txt(self.latest_result, output_dir)
            self.export_dir = output_dir
            self.status_var.set(f'导出完成：{file_path}')
            messagebox.showinfo('导出成功', f'已导出到：\n{file_path}')
        except Exception as exc:
            messagebox.showerror('导出失败', f'导出 txt 失败：{exc}')

    @staticmethod
    def _fill_listbox(listbox, values):
        listbox.delete(0, tk.END)
        for value in values:
            listbox.insert(tk.END, value)


def run_app():
    root = tk.Tk()
    XiaoETongApp(root)
    root.mainloop()
