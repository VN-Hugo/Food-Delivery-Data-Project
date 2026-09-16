-- =====================================================================
-- Phase 2 · Step 6 — Read-only access for Power BI
-- Run in Snowsight as ACCOUNTADMIN after 01_setup.sql.
-- Connect Power BI to ZOMATO.MARTS with a user granted POWERBI_ROLE.
-- =====================================================================
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS POWERBI_ROLE;

-- Power BI can use the warehouse but cannot resize or modify it.
GRANT USAGE ON WAREHOUSE ZOMATO_WH TO ROLE POWERBI_ROLE;

-- Database and Gold schema visibility.
GRANT USAGE ON DATABASE ZOMATO TO ROLE POWERBI_ROLE;
GRANT USAGE ON SCHEMA ZOMATO.MARTS TO ROLE POWERBI_ROLE;

-- Existing dbt mart tables and views.
GRANT SELECT ON ALL TABLES IN SCHEMA ZOMATO.MARTS TO ROLE POWERBI_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA ZOMATO.MARTS TO ROLE POWERBI_ROLE;

-- Keep access working when dbt creates or replaces marts later.
GRANT SELECT ON FUTURE TABLES IN SCHEMA ZOMATO.MARTS TO ROLE POWERBI_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA ZOMATO.MARTS TO ROLE POWERBI_ROLE;

-- Optional: grant the role to a dedicated Snowflake service user.
-- Replace POWERBI_USER with the actual Snowflake username before running.

USE ROLE ACCOUNTADMIN;

-- 1. Tạo user mới 
CREATE USER POWERBI_USER
  PASSWORD = 'Mat Khau Cua Ban' 
  LOGIN_NAME = 'POWERBI_USER'
  DISPLAY_NAME = 'Power BI Service Account'
  MUST_CHANGE_PASSWORD = FALSE; 

-- 2. Gán quyền (Role) bạn vừa tạo ở bước trước cho User này
GRANT ROLE POWERBI_ROLE TO USER POWERBI_USER;

-- 3. Cài đặt Role và Warehouse mặc định để Power BI kết nối trơn tru hơn
ALTER USER POWERBI_USER SET DEFAULT_ROLE = POWERBI_ROLE;
ALTER USER POWERBI_USER SET DEFAULT_WAREHOUSE = ZOMATO_WH;