-- Create a location table.
DELIMITER $$

DROP PROCEDURE IF EXISTS `loop`.`temp_migration_function` $$
CREATE PROCEDURE `loop`.`temp_migration_function`()
BEGIN

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'location') IS NULL THEN 
    CREATE TABLE `location` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `google_id` VARCHAR(255) NULL,
        `address` VARCHAR(255) NULL,
        `display_name` VARCHAR(255) NULL,
        `latitude` FLOAT NOT NULL,
        `longitude` FLOAT NOT NULL,
        `created` DATETIME DEFAULT(sysdate()),
        `last_updated` DATETIME DEFAULT(sysdate()),
        PRIMARY KEY (`id`)
    );
ALTER TABLE `location` ADD UNIQUE unique_google_id(
        `google_id`
);
END IF;

END $$

CALL `loop`.`temp_migration_function`() $$
DROP PROCEDURE `loop`.`temp_migration_function` $$

DELIMITER ;