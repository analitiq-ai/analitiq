-- Create the aggregate table for user activity summary
CREATE TABLE user_activity_summary AS
SELECT
    u.userid,
    u.username,
    u.firstname,
    u.lastname,
    u.city,
    u.state,
    COUNT(DISTINCT l.listid) AS total_listings,
    COUNT(DISTINCT s.salesid) AS total_sales,
    SUM(s.qtysold) AS total_tickets_sold,
    SUM(s.pricepaid) AS total_revenue,
    AVG(s.commission) AS avg_commission_earned
FROM
    users u
        LEFT JOIN listing l ON u.userid = l.sellerid
        LEFT JOIN sales s ON l.listid = s.listid
GROUP BY
    u.userid,
    u.username,
    u.firstname,
    u.lastname,
    u.city,
    u.state;

-- Query to validate the aggregate table
SELECT * FROM user_activity_summary;
