from kubernetes import config, client
from kubernetes.stream import stream
from kubernetes.client.api import core_v1_api


config.load_kube_config()

api_instance = core_v1_api.CoreV1Api()



v1 = client.CoreV1Api()
ret = v1.list_pod_for_all_namespaces(watch=False)


first_row = f"{'NAME' : <45} | {'NAMESPACE' : <25} | {'IP' : <15} | {'NODE' : <50} | {'MEM (MB)' : <15} | {'MEM (%)': <6} | {'START TIME' : <20}"

print(first_row)
print("-" * len(first_row))

for i in ret.items:
    if i.metadata.namespace != "aamazon-cloudwatch":
        ip          = i.status.pod_ip
        namespace   = i.metadata.namespace
        name        = i.metadata.name
        node        = i.spec.node_name
        start_time  = str(i.status.start_time)[:-6]
        
        exec_command = ['/bin/sh']
        
        
        memory_usage    = 'ERROR'
        cpu_usage       = 'ERROR'
        
        try: 
        
            resp = stream(api_instance.connect_get_namespaced_pod_exec,
                      name,
                      namespace,
                      command=exec_command,
                      stderr=True, stdin=True,
                      stdout=True, tty=False,
                      _preload_content=False)
                      
            commands = ['cat /sys/fs/cgroup/memory/memory.usage_in_bytes',
                        'cat /sys/fs/cgroup/cpu/cpuacct.usage']
            
            usage_vars = [memory_usage, cpu_usage]
            
            cnt = 0
        

            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    usage_vars[cnt] = str(int(resp.read_stdout())/1048576)
                    cnt = cnt + 1
                if resp.peek_stderr():
                    usage_vars[cnt] = str(resp.read_stderr())[:20]
                    cnt = cnt + 1
                if commands:
                    c = commands.pop(0)
                    resp.write_stdin(c + "\n")
                else:
                    break
                
                memory_usage = usage_vars[0]
                
        except:
            memory_usage = 0.1
            
        try:

            CRED = '\033[41m' if float(memory_usage) > 1000 else '\033[42m'
        
        except:
            CRED = '\033[42m'
            
        CEND = '\033[0m'
        
        try:
        
            print(f'{name : <45} | {namespace : <25} | {ip : <15} | {node : <50} | {CRED}{memory_usage : <15}{CEND} | {CRED}{int(float(memory_usage)/1600*100) : <7}{CEND} | {start_time}')
        except:
            pass
