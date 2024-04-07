-- Create a rating table.
DELIMITER $$

DROP PROCEDURE IF EXISTS `loop`.`temp_migration_function` $$
CREATE PROCEDURE `loop`.`temp_migration_function`()
BEGIN

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'rating') IS NULL THEN 
    CREATE TABLE `rating` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `price` INT NULL,
        `vibe` INT NULL,
        `food` INT NULL,
        `location` INT NULL,
        `user` INT NULL,
        `created` DATETIME DEFAULT(sysdate()),
        `last_updated` DATETIME DEFAULT(sysdate()),
        FOREIGN KEY (`location`) REFERENCES `location`(`id`),
        FOREIGN KEY (`user`) REFERENCES `user`(`id`),
        PRIMARY KEY (`id`)
    );
END IF;

END $$

CALL `loop`.`temp_migration_function`() $$
DROP PROCEDURE `loop`.`temp_migration_function` $$

DELIMITER ;