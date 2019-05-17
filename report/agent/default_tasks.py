# encoding=utf8

default_tasks = [
    {
        "task_id": "001",
        "task_name": "服务器资源统计日报",
        "task_type": "monitor",
        "task_period": 'day',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["node.cpu.total.percent", "node.mem.percent",\
                "partition.percent", "node.swap.percent"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "002",
        "task_name": "服务器资源统计周报",
        "task_type": "monitor",
        "task_period": 'week',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["node.cpu.total.percent", "node.mem.percent",\
            "partition.percent", "node.swap.percent"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "003",
        "task_name": "服务器资源统计月报",
        "task_type": "monitor",
        "task_period": 'month',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["node.cpu.total.percent", "node.mem.percent",\
            "partition.percent", "node.swap.percent"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "004",
        "task_name": "Openstack集群分析日报",
        "task_type": "meter",
        "task_period": 'day',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["user_statistics",  "vm_statistics"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "005",
        "task_name": "Openstack集群分析周报",
        "task_type": "meter",
        "task_period": 'week',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["user_statistics",  "vm_statistics"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "006",
        "task_name": "Openstack集群分析月报",
        "task_type": "meter",
        "task_period": 'month',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["user_statistics",  "vm_statistics"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "007",
        "task_name": "告警数据日报",
        "task_type": "alarm",
        "task_period": 'day',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["host distribute", "user distribute",\
                "type distribute",  "severity distribute", "time distribute",\
                "response time distribute"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "008",
        "task_name": "告警数据周报",
        "task_type": "alarm",
        "task_period": 'week',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["host distribute", "user distribute",\
                "type distribute",  "severity distribute", "time distribute",\
                "response time distribute"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
    {
        "task_id": "009",
        "task_name": "告警数据月报",
        "task_type": "alarm",
        "task_period": 'month',
        "task_time": "",
        "task_status": "Active",
        "task_language": "Chinese",
        "task_content": '{"meterlist":["host distribute", "user distribute",\
                "type distribute",  "severity distribute", "time distribute",\
                "response time distribute"]}',
        "task_metadata": '{"filetype":"pdf", "needmail":"N"}'
    },
]
