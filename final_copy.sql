-- MySQL dump 10.13  Distrib 8.0.37, for Win64 (x86_64)
--
-- Host: localhost    Database: kjsce_timetable
-- ------------------------------------------------------
-- Server version	8.0.37

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
-- Table structure for table `all_timetables`
--

DROP TABLE IF EXISTS `all_timetables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `all_timetables` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `year` varchar(500) NOT NULL,
  `sem` varchar(500) NOT NULL,
  `year_sem` varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `year_sem` (`year_sem`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `all_timetables`
--

LOCK TABLES `all_timetables` WRITE;
/*!40000 ALTER TABLE `all_timetables` DISABLE KEYS */;
INSERT INTO `all_timetables` VALUES (13,'2024_2025','ODD','ODD_2024_2025');
/*!40000 ALTER TABLE `all_timetables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `divisions`
--

DROP TABLE IF EXISTS `divisions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `divisions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `year` varchar(10) NOT NULL,
  `course` varchar(100) NOT NULL,
  `department` varchar(100) NOT NULL,
  `batch` varchar(10) NOT NULL,
  `no_of_div` int NOT NULL,
  `class` varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `divisions`
--

--
-- Table structure for table `faculty`
--

DROP TABLE IF EXISTS `faculty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `faculty` (
  `facid` bigint unsigned NOT NULL AUTO_INCREMENT,
  `facinit` varchar(10) NOT NULL,
  `facname` varchar(500) NOT NULL,
  `facdes` varchar(500) NOT NULL,
  `facqual` varchar(500) NOT NULL,
  `facdep` varchar(500) NOT NULL,
  `facshdep` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`facid`),
  UNIQUE KEY `facid` (`facid`),
  UNIQUE KEY `facinit` (`facinit`)
) ENGINE=InnoDB AUTO_INCREMENT=311 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faculty`
--



--
-- Table structure for table `odd_2024_2025`
--

DROP TABLE IF EXISTS `odd_2024_2025`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `odd_2024_2025` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `class` varchar(250) NOT NULL,
  `subject` varchar(500) NOT NULL,
  `slot` varchar(50) NOT NULL,
  `day` varchar(250) NOT NULL,
  `time` varchar(250) NOT NULL,
  `faculty` varchar(250) NOT NULL,
  `room` varchar(250) NOT NULL,
  `batch` varchar(200) NOT NULL,
  `type` varchar(100) NOT NULL,
  `branch` varchar(250) NOT NULL,
  `division` varchar(250) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3574 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `odd_2024_2025`
--



--
-- Table structure for table `rooms`
--

DROP TABLE IF EXISTS `rooms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rooms` (
  `roomid` bigint unsigned NOT NULL AUTO_INCREMENT,
  `roomno` varchar(100) NOT NULL,
  `roomdes` varchar(500) NOT NULL,
  `roomdep` varchar(500) NOT NULL,
  `roomshdep` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`roomid`),
  UNIQUE KEY `roomid` (`roomid`),
  UNIQUE KEY `roomno` (`roomno`)
) ENGINE=InnoDB AUTO_INCREMENT=3964 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rooms`
--

LOCK TABLES `rooms` WRITE;
/*!40000 ALTER TABLE `rooms` DISABLE KEYS */;

--
-- Table structure for table `subjects`
--

DROP TABLE IF EXISTS `subjects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subjects` (
  `subid` bigint unsigned NOT NULL AUTO_INCREMENT,
  `subclass` varchar(500) NOT NULL,
  `subsem` varchar(500) NOT NULL,
  `subcode` varchar(500) NOT NULL,
  `subabb` varchar(500) NOT NULL,
  `subname` varchar(500) NOT NULL,
  `sublecture` int NOT NULL,
  `subtut` int NOT NULL,
  `subprac` int NOT NULL,
  `subelective` varchar(500) NOT NULL,
  `subdep` varchar(500) NOT NULL,
  PRIMARY KEY (`subid`),
  UNIQUE KEY `subid` (`subid`),
  UNIQUE KEY `subcode` (`subcode`)
) ENGINE=InnoDB AUTO_INCREMENT=3578 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subjects`
--



--
-- Table structure for table `temp_data`
--

DROP TABLE IF EXISTS `temp_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_data` (
  `id` bigint unsigned NOT NULL,
  `class` varchar(250) NOT NULL,
  `subject` varchar(500) NOT NULL,
  `slot` varchar(50) NOT NULL,
  `day` varchar(250) NOT NULL,
  `time` varchar(250) NOT NULL,
  `faculty` varchar(250) NOT NULL,
  `room` varchar(250) NOT NULL,
  `batch` varchar(200) NOT NULL,
  `type` varchar(100) NOT NULL,
  `branch` varchar(250) NOT NULL,
  `division` varchar(250) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `temp_data`
--


--
-- Table structure for table `time_slots`
--

DROP TABLE IF EXISTS `time_slots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `time_slots` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `slots_name` varchar(500) NOT NULL,
  `day` varchar(250) DEFAULT NULL,
  `time` varchar(500) DEFAULT NULL,
  `slot_time_day` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `slots_name` (`slots_name`)
) ENGINE=InnoDB AUTO_INCREMENT=226 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `time_slots`
--

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email_id` varchar(100) NOT NULL,
  `user_password` varchar(100) NOT NULL,
  `college_name` varchar(100) NOT NULL,
  `department_name` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email_id` (`email_id`),
  UNIQUE KEY `department_name` (`department_name`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--


/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-07-04 17:41:39
