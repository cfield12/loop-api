-- Create friend status + friend tables.
DELIMITER $$

DROP PROCEDURE IF EXISTS `loop`.`temp_migration_function` $$
CREATE PROCEDURE `loop`.`temp_migration_function`()
BEGIN

IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'friend_status') IS NULL THEN
    CREATE TABLE `friend_status` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `description` VARCHAR(255) NULL,
    PRIMARY KEY (`id`)
    );

END IF;

INSERT INTO `loop`.`friend_status` (description)
SELECT 'Friends'
WHERE NOT EXISTS (SELECT 1 FROM `loop`.`friend_status` WHERE description = 'Friends');

INSERT INTO `loop`.`friend_status` (description)
SELECT 'Pending'
WHERE NOT EXISTS (SELECT 1 FROM `loop`.`friend_status` WHERE description = 'Pending');

INSERT INTO `loop`.`friend_status` (description)
SELECT 'Blocked'
WHERE NOT EXISTS (SELECT 1 FROM `loop`.`friend_status` WHERE description = 'Blocked');


IF (SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = 'loop' AND table_name = 'friend') IS NULL THEN
    CREATE TABLE `friend` (
        `id` INT NOT NULL AUTO_INCREMENT,
        `friend_1` INT NOT NULL,
        `friend_2` INT NOT NULL,
        `status` INT NOT NULL,
        `created` DATETIME DEFAULT(sysdate()),
        `last_updated` DATETIME DEFAULT(sysdate()),
        FOREIGN KEY (`friend_1`) REFERENCES `user`(`id`),
        FOREIGN KEY (`friend_2`) REFERENCES `user`(`id`),
        FOREIGN KEY (`status`) REFERENCES `friend_status`(`id`),
        PRIMARY KEY (`id`)
    );
ALTER TABLE `friend` ADD UNIQUE unique_friendship_1(
        `friend_1`, `friend_2`
);
ALTER TABLE `friend` ADD UNIQUE unique_friendship_2(
        `friend_2`, `friend_1`
);
END IF;

END $$

CALL `loop`.`temp_migration_function`() $$
DROP PROCEDURE `loop`.`temp_migration_function` $$

DELIMITER ;