-- Create a user table.
DELIMITER $$

DROP PROCEDURE IF EXISTS `loop`.`temp_migration_function` $$
CREATE PROCEDURE `loop`.`temp_migration_function`()
BEGIN

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'user') IS NULL THEN 
    CREATE TABLE `user` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `cognito_user_name` VARCHAR(255) NULL,
        `first_name` VARCHAR(255) NULL,
        `last_name` VARCHAR(255) NULL,
        `created` DATETIME DEFAULT(sysdate()),
        `last_updated` DATETIME DEFAULT(sysdate()),
        PRIMARY KEY (`id`)
    );
ALTER TABLE `user` ADD UNIQUE unique_cognito_user_name(
        `cognito_user_name`
);
END IF;

END $$

CALL `loop`.`temp_migration_function`() $$
DROP PROCEDURE `loop`.`temp_migration_function` $$

DELIMITER ;
