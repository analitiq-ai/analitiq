/*
 Navicat Premium Data Transfer

 Source Server         : localhost_5432
 Source Server Type    : PostgreSQL
 Source Server Version : 140011 (140011)
 Source Host           : localhost:5432
 Source Catalog        : app
 Source Schema         : schema1

 Target Server Type    : PostgreSQL
 Target Server Version : 140011 (140011)
 File Encoding         : 65001

 Date: 06/06/2024 04:12:16
*/


-- ----------------------------
-- Table structure for table1
-- ----------------------------
DROP TABLE IF EXISTS "schema1"."table1";
CREATE TABLE "schema1"."table1" (
  "column1" text COLLATE "pg_catalog"."default",
  "column2" int4
)
;

-- ----------------------------
-- Records of table1
-- ----------------------------

-- ----------------------------
-- Table structure for table2
-- ----------------------------
DROP TABLE IF EXISTS "schema1"."table2";
CREATE TABLE "schema1"."table2" (
  "column1" text COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Records of table2
-- ----------------------------
