-- Create a group and user group tables.
DELIMITER $$

DROP PROCEDURE IF EXISTS `loop`.`temp_migration_function` $$
CREATE PROCEDURE `loop`.`temp_migration_function`()
BEGIN

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'group') IS NULL THEN
    CREATE TABLE `group` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `description` VARCHAR(255) NULL,
    PRIMARY KEY (`id`)
    );

END IF;

INSERT INTO `loop`.`group` (description)
SELECT 'loop_admin'
WHERE NOT EXISTS (SELECT 1 FROM `loop`.`group` WHERE description = 'loop_admin');

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'group_user') IS NULL THEN
    CREATE TABLE `group_user` (
        `user` INT NOT NULL,
        `group` INT NOT NULL,
        FOREIGN KEY (`user`) REFERENCES `user`(`id`),
        FOREIGN KEY (`group`) REFERENCES `group`(`id`),
    PRIMARY KEY (`user`, `group`)
    );

END IF;

END $$

CALL `loop`.`temp_migration_function`() $$
DROP PROCEDURE `loop`.`temp_migration_function` $$

DELIMITER ;