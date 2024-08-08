-- Create the aggregate table for event attendance and sales summary
CREATE TABLE event_attendance_sales_summary AS
SELECT
    e.eventid,
    e.eventname,
    e.starttime,
    v.venuename,
    v.venuecity,
    v.venuestate,
    c.catgroup,
    c.catname,
    c.catdesc,
    d.caldate,
    d.day,
    d.week,
    d.month,
    d.qtr,
    d.year,
    SUM(s.qtysold) AS total_tickets_sold,
    SUM(s.pricepaid) AS total_revenue,
    AVG(s.pricepaid / s.qtysold) AS avg_price_per_ticket,
    COUNT(s.salesid) AS total_sales_transactions
FROM
    event e
        JOIN venue v ON e.venueid = v.venueid
        JOIN category c ON e.catid = c.catid
        JOIN date d ON e.dateid = d.dateid
        LEFT JOIN sales s ON e.eventid = s.eventid
GROUP BY
    e.eventid,
    e.eventname,
    e.starttime,
    v.venuename,
    v.venuecity,
    v.venuestate,
    c.catgroup,
    c.catname,
    c.catdesc,
    d.caldate,
    d.day,
    d.week,
    d.month,
    d.qtr,
    d.year;

-- Query to validate the aggregate table
SELECT * FROM event_attendance_sales_summary;
