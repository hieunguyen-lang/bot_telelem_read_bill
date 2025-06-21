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
-- Table structure for table `thong_tin_hoa_don_rut`
--

DROP TABLE IF EXISTS `thong_tin_hoa_don_rut`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `thong_tin_hoa_don_rut` (
  `id` int NOT NULL AUTO_INCREMENT,
  `thoi_gian` datetime DEFAULT NULL,
  `nguoi_gui` varchar(255) DEFAULT NULL,
  `ten_khach` varchar(255) DEFAULT NULL,
  `so_dien_thoai` varchar(20) DEFAULT NULL,
  `so_tien_rut` varchar(50) DEFAULT NULL,
  `phan_tram_phi` varchar(20) DEFAULT NULL,
  `so_tien_phi` varchar(50) DEFAULT NULL,
  `so_tien_chuyen_khoan` varchar(50) DEFAULT NULL,
  `lich_canh_bao` varchar(50) DEFAULT NULL,
  `so_tai_khoan` text,
  `ghi_chu` text,
  `ngan_hang` varchar(100) DEFAULT NULL,
  `don_vi_ban` varchar(255) DEFAULT NULL,
  `dia_chi_don_vi` text,
  `ngay_giao_dich` varchar(50) DEFAULT NULL,
  `gio_giao_dich` varchar(50) DEFAULT NULL,
  `tong_so_tien` varchar(50) DEFAULT NULL,
  `don_vi_tien_te` varchar(10) DEFAULT NULL,
  `loai_the` varchar(50) DEFAULT NULL,
  `ma_giao_dich` varchar(100) DEFAULT NULL,
  `ma_don_vi_chap_nhan` varchar(100) DEFAULT NULL,
  `so_lo` varchar(50) DEFAULT NULL,
  `so_tham_chieu` varchar(100) DEFAULT NULL,
  `loai_giao_dich` varchar(100) DEFAULT NULL,
  `caption_goc` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `thong_tin_hoa_don_rut`
--

LOCK TABLES `thong_tin_hoa_don_rut` WRITE;
/*!40000 ALTER TABLE `thong_tin_hoa_don_rut` DISABLE KEYS */;
INSERT INTO `thong_tin_hoa_don_rut` VALUES (1,'1970-02-01 00:00:00','5435','5345',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `thong_tin_hoa_don_rut` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-21 14:49:49
