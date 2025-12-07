#!/usr/bin/env python3
"""
清理遗留的 realtime_algorithm_service 进程
用于清理那些在后台偷偷运行的进程

使用方法:
    python cleanup_orphaned_processes.py [task_id]
    
如果不指定 task_id，将清理所有相关的遗留进程
"""
import os
import sys
import subprocess
import signal
import argparse

def cleanup_orphaned_processes(task_id=None):
    """清理遗留的进程"""
    target_script = 'run_deploy.py'
    
    try:
        import psutil
        
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                # 检查是否是run_deploy.py进程
                if target_script not in ' '.join(cmdline):
                    continue
                
                # 检查环境变量
                is_target = False
                try:
                    environ = proc.info.get('environ', {})
                    if environ:
                        proc_task_id = environ.get('TASK_ID')
                        if task_id is None:
                            # 清理所有相关进程
                            is_target = True
                        elif proc_task_id == str(task_id):
                            is_target = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 如果无法获取环境变量，检查命令行参数
                    if task_id is None or f'TASK_ID={task_id}' in ' '.join(cmdline):
                        is_target = True
                
                if is_target:
                    try:
                        print(f"🔍 发现遗留进程: PID={proc.info['pid']}, CMD={' '.join(cmdline[:3])}...")
                        
                        # 获取进程组ID
                        pgid = os.getpgid(proc.info['pid'])
                        print(f"   进程组ID: {pgid}")
                        
                        # 先尝试优雅终止整个进程组
                        os.killpg(pgid, signal.SIGTERM)
                        import time
                        time.sleep(2)
                        
                        # 检查是否还在运行
                        try:
                            proc.wait(timeout=1)
                            print(f"✅ 遗留进程 {proc.info['pid']} 已优雅终止")
                        except psutil.TimeoutExpired:
                            # 强制终止
                            os.killpg(pgid, signal.SIGKILL)
                            time.sleep(0.5)
                            print(f"⚠️ 遗留进程 {proc.info['pid']} 已强制终止")
                        
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError, OSError) as e:
                        print(f"⚠️ 无法终止进程 {proc.info['pid']}: {str(e)}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            print(f"\n✅ 清理了 {killed_count} 个遗留进程")
        else:
            print(f"\n✅ 未发现遗留进程")
            
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
                pids_to_kill = []
                for line in lines:
                    if target_script in line:
                        if task_id is None or f'TASK_ID={task_id}' in line:
                            parts = line.split()
                            if len(parts) > 1:
                                try:
                                    pid = int(parts[1])
                                    pids_to_kill.append(pid)
                                except ValueError:
                                    pass
                
                if pids_to_kill:
                    print(f"🔍 发现 {len(pids_to_kill)} 个遗留进程: {pids_to_kill}")
                    for pid in pids_to_kill:
                        try:
                            # 终止进程组
                            pgid = os.getpgid(pid)
                            print(f"   终止进程组 {pgid} (主进程PID: {pid})")
                            os.killpg(pgid, signal.SIGTERM)
                            import time
                            time.sleep(2)
                            # 如果还在运行，强制终止
                            try:
                                os.killpg(pgid, signal.SIGKILL)
                            except:
                                pass
                            print(f"✅ 遗留进程 {pid} 已终止")
                        except (ProcessLookupError, OSError) as e:
                            print(f"⚠️ 无法终止进程 {pid}: {str(e)}")
                    print(f"\n✅ 清理了 {len(pids_to_kill)} 个遗留进程")
                else:
                    print(f"\n✅ 未发现遗留进程")
        except Exception as e:
            print(f"❌ 清理遗留进程失败: {str(e)}")
    except Exception as e:
        print(f"❌ 清理遗留进程时出错: {str(e)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='清理遗留的 realtime_algorithm_service 进程')
    parser.add_argument('task_id', type=int, nargs='?', help='任务ID（可选，不指定则清理所有相关进程）')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧹 清理遗留的 realtime_algorithm_service 进程")
    print("=" * 60)
    
    if args.task_id:
        print(f"📋 清理任务ID: {args.task_id}")
    else:
        print("📋 清理所有相关进程")
    
    print("=" * 60)
    
    cleanup_orphaned_processes(args.task_id)
    
    print("=" * 60)

