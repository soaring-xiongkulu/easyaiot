#!/usr/bin/env python3
"""
强制关闭所有 realtime_algorithm_service 相关进程
包括 run_deploy.py 主进程和所有 FFmpeg 子进程

使用方法:
    python kill_all_realtime_processes.py [--force] [--task-id TASK_ID]
    
选项:
    --force: 强制终止，不等待优雅退出
    --task-id: 只关闭指定任务ID的进程（不指定则关闭所有）
"""
import os
import sys
import subprocess
import signal
import argparse
import time

def find_realtime_processes(task_id=None):
    """查找所有 realtime_algorithm_service 相关进程"""
    processes = []
    target_script = 'run_deploy.py'
    
    try:
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join(cmdline)
                is_target = False
                proc_task_id = None
                
                # 检查是否是 run_deploy.py 进程
                if target_script in cmdline_str:
                    # 尝试获取环境变量
                    try:
                        environ = proc.environ()
                        proc_task_id = environ.get('TASK_ID')
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 如果无法获取环境变量，从命令行参数中提取
                        for arg in cmdline:
                            if 'TASK_ID=' in str(arg):
                                try:
                                    proc_task_id = str(arg).split('TASK_ID=')[1].split()[0]
                                except:
                                    pass
                    
                    if task_id is None:
                        is_target = True
                    elif proc_task_id == str(task_id):
                        is_target = True
                
                # 检查是否是 FFmpeg 进程（可能是 run_deploy.py 的子进程）
                elif 'ffmpeg' in cmdline_str.lower():
                    try:
                        # 检查父进程是否是 run_deploy.py
                        parent = proc.parent()
                        if parent:
                            parent_cmdline = ' '.join(parent.cmdline())
                            if target_script in parent_cmdline:
                                # 检查父进程的环境变量
                                try:
                                    parent_environ = parent.environ()
                                    parent_task_id = parent_environ.get('TASK_ID')
                                except:
                                    parent_task_id = None
                                
                                if task_id is None:
                                    is_target = True
                                elif parent_task_id == str(task_id):
                                    is_target = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                if is_target:
                    # 获取进程组ID（pgid不能通过process_iter获取，需要直接访问）
                    try:
                        pgid = proc.pgid
                    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                        pgid = None
                    
                    processes.append({
                        'pid': proc.info['pid'],
                        'ppid': proc.info.get('ppid'),
                        'pgid': pgid,
                        'cmdline': cmdline_str[:100],  # 只取前100个字符
                        'task_id': proc_task_id,
                        'proc': proc
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
        
    except ImportError:
        # psutil未安装，使用ps命令（Linux）
        print("⚠️ psutil未安装，使用ps命令查找进程...")
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if target_script in line or 'ffmpeg' in line.lower():
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                ppid = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                                
                                # 检查是否匹配任务ID
                                if task_id is None or f'TASK_ID={task_id}' in line:
                                    processes.append({
                                        'pid': pid,
                                        'ppid': ppid,
                                        'pgid': None,  # ps命令无法直接获取pgid
                                        'cmdline': line[:100],
                                        'task_id': None,
                                        'proc': None
                                    })
                            except (ValueError, IndexError):
                                pass
        except Exception as e:
            print(f"❌ 查找进程失败: {str(e)}")
        
        return processes


def kill_process_group(pgid, force=False):
    """终止进程组"""
    try:
        if not force:
            # 先尝试优雅终止
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(2)
            # 检查进程组是否还存在
            try:
                os.killpg(pgid, 0)  # 发送信号0检查进程是否存在
                # 如果还存在，强制终止
                os.killpg(pgid, signal.SIGKILL)
                time.sleep(0.5)
            except ProcessLookupError:
                # 进程组已不存在
                pass
        else:
            # 直接强制终止
            os.killpg(pgid, signal.SIGKILL)
            time.sleep(0.5)
        return True
    except (ProcessLookupError, OSError) as e:
        return False


def kill_all_realtime_processes(force=False, task_id=None):
    """关闭所有 realtime_algorithm_service 相关进程"""
    print("=" * 70)
    print("🔍 正在查找 realtime_algorithm_service 相关进程...")
    print("=" * 70)
    
    processes = find_realtime_processes(task_id)
    
    if not processes:
        print("✅ 未发现相关进程")
        return
    
    print(f"\n📋 发现 {len(processes)} 个相关进程:\n")
    
    # 按进程组分组
    process_groups = {}
    standalone_processes = []
    
    for proc_info in processes:
        pgid = proc_info.get('pgid')
        pid = proc_info['pid']
        
        if pgid:
            if pgid not in process_groups:
                process_groups[pgid] = []
            process_groups[pgid].append(proc_info)
        else:
            # 如果没有pgid，尝试获取
            try:
                pgid = os.getpgid(pid)
                if pgid not in process_groups:
                    process_groups[pgid] = []
                process_groups[pgid].append(proc_info)
            except (ProcessLookupError, OSError):
                standalone_processes.append(proc_info)
    
    # 显示进程信息
    for pgid, group_procs in process_groups.items():
        print(f"📦 进程组 {pgid} ({len(group_procs)} 个进程):")
        for proc_info in group_procs:
            task_id_str = f" (TASK_ID={proc_info['task_id']})" if proc_info['task_id'] else ""
            print(f"   - PID: {proc_info['pid']:>6}, PPID: {proc_info.get('ppid', 'N/A'):>6}{task_id_str}")
            print(f"     命令: {proc_info['cmdline'][:80]}...")
        print()
    
    for proc_info in standalone_processes:
        task_id_str = f" (TASK_ID={proc_info['task_id']})" if proc_info['task_id'] else ""
        print(f"📦 独立进程:")
        print(f"   - PID: {proc_info['pid']:>6}, PPID: {proc_info.get('ppid', 'N/A'):>6}{task_id_str}")
        print(f"     命令: {proc_info['cmdline'][:80]}...")
        print()
    
    # 确认
    if not force:
        response = input(f"\n⚠️  确定要终止这 {len(processes)} 个进程吗？(yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ 已取消")
            return
    
    print("\n" + "=" * 70)
    print("🛑 开始终止进程...")
    print("=" * 70)
    
    killed_count = 0
    failed_count = 0
    
    # 先终止进程组
    for pgid, group_procs in process_groups.items():
        print(f"\n📦 终止进程组 {pgid} ({len(group_procs)} 个进程)...")
        if kill_process_group(pgid, force):
            killed_count += len(group_procs)
            print(f"   ✅ 进程组 {pgid} 已终止")
        else:
            failed_count += len(group_procs)
            print(f"   ❌ 进程组 {pgid} 终止失败")
    
    # 再终止独立进程
    for proc_info in standalone_processes:
        pid = proc_info['pid']
        print(f"\n📦 终止独立进程 PID={pid}...")
        try:
            if not force:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # 检查是否还存在
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                os.kill(pid, signal.SIGKILL)
            killed_count += 1
            print(f"   ✅ 进程 {pid} 已终止")
        except (ProcessLookupError, OSError) as e:
            failed_count += 1
            print(f"   ❌ 进程 {pid} 终止失败: {str(e)}")
    
    # 等待一下，然后再次检查是否还有遗留进程
    time.sleep(1)
    remaining_processes = find_realtime_processes(task_id)
    
    print("\n" + "=" * 70)
    if remaining_processes:
        print(f"⚠️  仍有 {len(remaining_processes)} 个进程未终止，尝试强制终止...")
        for proc_info in remaining_processes:
            pid = proc_info['pid']
            try:
                try:
                    pgid = os.getpgid(pid)
                    os.killpg(pgid, signal.SIGKILL)
                except:
                    os.kill(pid, signal.SIGKILL)
                print(f"   ✅ 强制终止进程 {pid}")
                killed_count += 1
            except (ProcessLookupError, OSError):
                pass
        time.sleep(0.5)
        remaining_processes = find_realtime_processes(task_id)
    
    if remaining_processes:
        print(f"❌ 仍有 {len(remaining_processes)} 个进程无法终止:")
        for proc_info in remaining_processes:
            print(f"   - PID: {proc_info['pid']}")
    else:
        print(f"✅ 成功终止 {killed_count} 个进程")
        if failed_count > 0:
            print(f"⚠️  {failed_count} 个进程终止失败（可能已经不存在）")
    print("=" * 70)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='强制关闭所有 realtime_algorithm_service 相关进程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 关闭所有相关进程（需要确认）
  python kill_all_realtime_processes.py
  
  # 强制关闭所有相关进程（不需要确认）
  python kill_all_realtime_processes.py --force
  
  # 只关闭指定任务ID的进程
  python kill_all_realtime_processes.py --task-id 1
  
  # 强制关闭指定任务ID的进程
  python kill_all_realtime_processes.py --force --task-id 1
        """
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制终止，不等待优雅退出，也不需要确认'
    )
    parser.add_argument(
        '--task-id', '-t',
        type=int,
        help='只关闭指定任务ID的进程（不指定则关闭所有）'
    )
    
    args = parser.parse_args()
    
    try:
        kill_all_realtime_processes(force=args.force, task_id=args.task_id)
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

