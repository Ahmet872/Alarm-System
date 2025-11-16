-- ✅ FIXED - Proper DELIMITER syntax

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_cleanup_old_alarms(IN days_old INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_alarm_id INT;
    DECLARE cur CURSOR FOR 
        SELECT id 
        FROM alarms 
        WHERE status IN ('triggered', 'failed') 
        AND created_at < DATE_SUB(NOW(), INTERVAL days_old DAY);
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    START TRANSACTION;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_alarm_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        DELETE FROM alarms WHERE id = v_alarm_id;
    END LOOP;
    
    CLOSE cur;
    
    COMMIT;
END //

CREATE EVENT IF NOT EXISTS ev_cleanup_old_alarms
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
DO
    CALL sp_cleanup_old_alarms(30) //

DELIMITER ;