-- Read-only direct SQL comparisons for the Select AI storage rejection.
-- Run as DB_HEALTH_AGENT using the prescribed SQLcl.
select count(*) as row_count from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE;
select tablespace_name from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE;
select tablespace_name, used_percent from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE;
select tablespace_name, used_bytes, capacity_bytes from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE;
select tablespace_name, used_percent from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE where tablespace_name = 'DATA';
select sum(used_bytes) as total_used_bytes from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE;
select tablespace_name, used_percent from DB_HEALTH_AGENT.MONITOR_STORAGE_USAGE order by used_percent desc;
