-- MySQL dump 10.13  Distrib 8.4.5, for Linux (x86_64)
--
-- Host: localhost    Database: bill_data
-- ------------------------------------------------------
-- Server version	8.4.5

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `thong_tin_hoa_don`
--

DROP TABLE IF EXISTS `thong_tin_hoa_don`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thong_tin_hoa_don` (
  `id` int NOT NULL AUTO_INCREMENT,
  `thoi_gian` datetime DEFAULT NULL,
  `nguoi_gui` varchar(255) DEFAULT NULL,
  `ten_khach` varchar(255) DEFAULT NULL,
  `so_dien_thoai` varchar(20) DEFAULT NULL,
  `type_dao_rut` varchar(20) DEFAULT NULL,
  `ngan_hang` varchar(100) DEFAULT NULL,
  `ngay_giao_dich` varchar(50) DEFAULT NULL,
  `gio_giao_dich` varchar(50) DEFAULT NULL,
  `tong_so_tien` varchar(50) DEFAULT NULL,
  `so_the` varchar(100) DEFAULT NULL,
  `tid` varchar(50) DEFAULT NULL,
  `so_lo` varchar(100) DEFAULT NULL,
  `so_hoa_don` varchar(100) DEFAULT NULL,
  `ten_may_pos` varchar(100) DEFAULT NULL,
  `caption_goc` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `thong_tin_hoa_don`
--

LOCK TABLES `thong_tin_hoa_don` WRITE;
/*!40000 ALTER TABLE `thong_tin_hoa_don` DISABLE KEYS */;
INSERT INTO `thong_tin_hoa_don` VALUES (24,'2025-06-22 16:45:29','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(25,'2025-06-22 16:45:29','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(26,'2025-06-22 16:45:29','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(27,'2025-06-22 16:47:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(28,'2025-06-22 16:47:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(29,'2025-06-22 16:47:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(30,'2025-06-22 16:51:06','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5',NULL),(31,'2025-06-22 16:53:58','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(32,'2025-06-22 16:55:38','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(33,'2025-06-22 16:58:10','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(34,'2025-06-22 17:00:07','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(35,'2025-06-22 17:02:15','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(36,'2025-06-22 17:02:15','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(37,'2025-06-22 17:02:15','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(38,'2025-06-22 17:05:57','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-22','19:52:49','46150000','3564 19** **** 5142','19500296','000003','000005','GAS NGUYEN LONG 5','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(39,'2025-06-22 17:07:20','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(40,'2025-06-22 17:07:20','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(41,'2025-06-22 17:07:20','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(42,'2025-06-22 17:10:19','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2','Khach: {Đặng Huỳnh Duyệt}\nSdt: {0969963324}\nRut: {19M990}\nPhi: {2%}\nTienPhi: {400K}\nTong: {19M590}\nLichCanhBao: {21}\nNote: {Chuyển khoản hộ em với}'),(43,'2025-06-22 17:11:24','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(44,'2025-06-22 17:11:24','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(45,'2025-06-22 17:11:24','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(46,'2025-06-22 17:14:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(47,'2025-06-22 17:14:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(48,'2025-06-22 17:14:18','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(49,'2025-06-22 17:18:52','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(50,'2025-06-22 17:18:52','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(51,'2025-06-22 17:18:52','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(52,'2025-06-22 17:27:55','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(53,'2025-06-22 17:27:55','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(54,'2025-06-22 17:27:55','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(55,'2025-06-22 17:32:01','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(56,'2025-06-22 17:32:01','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(57,'2025-06-22 17:32:01','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(58,'2025-06-22 17:34:06','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(59,'2025-06-22 17:34:06','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(60,'2025-06-22 17:34:06','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(61,'2025-06-22 17:37:11','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(62,'2025-06-22 17:37:11','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(63,'2025-06-22 17:37:11','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL),(64,'2025-06-22 17:42:50','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:04:41','56300000','4696 **** **** 5541','02301043','000280','000454','XIXI GAMING 2',NULL),(65,'2025-06-22 17:42:50','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:05:10','56300000','3564 3302 8234 9250','02301043','000280','000455','XIXI GAMING 2',NULL),(66,'2025-06-22 17:42:50','hieunguyenkhac','Đặng Huỳnh Duyệt','0969963324','DAO','HDBank','2025-06-19','13:06:25','50200000','5138 9279 4277 0890','02301043','000280','000456','XIXI GAMING 2',NULL);
/*!40000 ALTER TABLE `thong_tin_hoa_don` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-23  0:04:51
