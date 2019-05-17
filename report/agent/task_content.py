# -*-coding:utf-8-*-
task_content = {
    "monitor":{
        "CPU":"CPU汇总数据:包括CPU总的使用率/系统CPU使用率/IOWait占比的平均值/ \
               最大值/最小值按照CPU平均值排序，展示CPU最大的TOPN物理机，并展示 \
               CPU使用详情，并列出占用资源最多的服务或者虚拟机",
        "mem":"内存统计汇总数据:包括平均值/最大值/最小值按照CPU平均值排序，\
               展示CPU最大的TOPN物理机，并展示CPU使用详情，并列出占用资源最多的 \
               服务或者虚拟机",
        "disk_partion":"主机磁盘分区的使用率增长趋势",
        "network_width":"主机各网卡的进出口流量趋势、丢包"
        },
    "alarm":{
        "alarm_data":"主机名、资源类型、总告警数量、各级别告警数量、各状态 \
                      告警数量",
        "host_distribute":"",
        "user_distribute":"",
        "type_distribute":"",
        "rank_distribute":"",
        "detail_alarm":"",
        "time_distribute":"",
        "response_time":""
        },
    "meter":{
        "resource_count":{"physical_resource":"计算、存储、网络总的资源池的容量，随时 \
                           间使用量的变化趋势:1.计算资源CPU/内存使用量变化趋势 \
                           2.存储资源已使用存储空间变化趋势 3.网络资源",
                          "vm_resource":"虚拟机，交换机，路由器，负载均衡，云硬盘"
                   },
        "user_count":{"each_user_resource":"",
                      "vm_bulid":"",
                      "用户在平台操作分析资源操作的数量，响应时间(平均,最小,最大)":"",
                      "quota_count":""
                   },
        "vm_count":{"vm_state":"",
                    "vm_type":"",
                    "vm_time":""
            }
        }
    }
