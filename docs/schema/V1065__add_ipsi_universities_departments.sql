-- BuildIt AI 입시상담 DB (2/4): 대학 기본정보 + 학과/모집단위 (신규 테이블만)
--
-- 대학 기본정보와 모집단위(학과)를 학년도 단위로 구조화한다.
-- 모든 행은 공식 출처 문서(ipsi_documents)와 연결되고 검증상태를 가진다.
--
-- 다음 마이그레이션 = V1066 (ipsi_admission_types / ipsi_recommended_subjects)

CREATE TABLE IF NOT EXISTS ipsi_universities (
  university_id BIGINT NOT NULL AUTO_INCREMENT,
  university_code VARCHAR(30) NULL COMMENT '교육부/대교협 대학코드(알면 기록)',
  name VARCHAR(160) NOT NULL COMMENT '대학명',
  english_name VARCHAR(200) NULL,
  region VARCHAR(80) NULL COMMENT '시도(지역)',
  establishment_type VARCHAR(30) NULL COMMENT '국립/공립/사립',
  admission_office_url VARCHAR(500) NULL COMMENT '입학처 공식 URL',
  source_document_id BIGINT NULL COMMENT '출처 문서(ipsi_documents)',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (university_id),
  KEY idx_ipsi_univ_name (name),
  KEY idx_ipsi_univ_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='대학 기본정보';

CREATE TABLE IF NOT EXISTS ipsi_departments (
  department_id BIGINT NOT NULL AUTO_INCREMENT,
  university_id BIGINT NOT NULL,
  academic_year VARCHAR(10) NOT NULL COMMENT '적용 학년도',
  department_name VARCHAR(200) NOT NULL COMMENT '학과/모집단위명',
  college_name VARCHAR(160) NULL COMMENT '단과대학/계열',
  campus VARCHAR(80) NOT NULL DEFAULT '' COMMENT '캠퍼스(없으면 빈 문자열-UNIQUE용)',
  source_document_id BIGINT NULL,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (department_id),
  CONSTRAINT uq_ipsi_department UNIQUE (university_id, academic_year, department_name, campus),
  KEY idx_ipsi_department_year (academic_year, verification_status),
  CONSTRAINT fk_ipsi_department_univ FOREIGN KEY (university_id)
    REFERENCES ipsi_universities (university_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='학과/모집단위(학년도 단위)';
