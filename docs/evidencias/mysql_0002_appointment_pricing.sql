--
-- Add field adjusted_price_cop to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `adjusted_price_cop` numeric(12, 0) NULL;
--
-- Add field catalog_price_cop to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `catalog_price_cop` numeric(12, 0) NULL;
--
-- Add field discount_amount_cop to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `discount_amount_cop` numeric(12, 0) NULL;
--
-- Add field discount_type to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `discount_type` varchar(7) NULL;
--
-- Add field discount_value to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `discount_value` numeric(14, 2) NULL;
--
-- Add field pricing_reason to appointment
--
ALTER TABLE `appointments_appointment` ADD COLUMN `pricing_reason` longtext NOT NULL;
