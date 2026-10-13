-- BuildIt AI 입시상담 DB (3/4): 전형(수시/정시) + 모집단위별 권장과목 (신규 테이블만)
--
-- ipsi_admission_types가 상담 DB의 핵심: 학년도·수시/정시·전형명/유형·모집인원·지원자격·
-- 학생부/수능 반영방법·최저학력기준·면접/논술/실기 조건을 한 행으로 구조화한다.
-- 모든 행은 공식 출처 문서 + 원문URL + 기관명 + 발표일 + 수집일 + 검증상태를 필수로 가진다.
--
-- 다음 마이그레이션 = V1067 (ipsi_schedules / ipsi_prior_results)

CREATE TABLE IF NOT EXISTS ipsi_admission_types (
  admission_type_id BIGINT NOT NULL AUTO_INCREMENT,
  university_id BIGINT NOT NULL,
  department_id BIGINT NULL COMMENT 'NULL=대학/계열 전체 전형',
  academic_year VARCHAR(10) NOT NULL COMMENT '적용 학년도',
  round_type VARCHAR(20) NOT NULL COMMENT 'SUSI(수시)/JEONGSI(정시)',
  type_name VARCHAR(200) NOT NULL COMMENT '전형명',
  type_category VARCHAR(60) NULL COMMENT '전형유형: 학생부교과/학생부종합/논술/실기/정원외 등',
  recruitment_count INT NULL COMMENT '모집인원',
  eligibility TEXT NULL COMMENT '지원자격',
  student_record_method TEXT NULL COMMENT '학생부 반영방법',
  suneung_method TEXT NULL COMMENT '수능 반영방법',
  min_academic_standard TEXT NULL COMMENT '수능 최저학력기준',
  interview_condition TEXT NULL COMMENT '면접 조건',
  essay_condition TEXT NULL COMMENT '논술 조건',
  practical_condition TEXT NULL COMMENT '실기 조건',
  source_document_id BIGINT NOT NULL COMMENT '공식 출처 문서',
  source_url VARCHAR(1000) NOT NULL COMMENT '원문 URL',
  institution_name VARCHAR(200) NOT NULL COMMENT '기관명',
  published_at DATE NULL COMMENT '발표일',
  collected_at DATETIME(6) NOT NULL COMMENT '수집일',
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED' COMMENT 'COLLECTED/EXTRACTED/NORMALIZED/REVIEW/APPROVED',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (admission_type_id),
  KEY idx_ipsi_admtype_lookup (university_id, academic_year, round_type),
  KEY idx_ipsi_admtype_year_status (academic_year, verification_status),
  KEY idx_ipsi_admtype_category (type_category),
  CONSTRAINT fk_ipsi_admtype_univ FOREIGN KEY (university_id)
    REFERENCES ipsi_universities (university_id) ON DELETE CASCADE,
  CONSTRAINT fk_ipsi_admtype_dept FOREIGN KEY (department_id)
    REFERENCES ipsi_departments (department_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='대학입학전형(수시/정시·전형명/유형·반영방법·최저·면접/논술/실기)';

CREATE TABLE IF NOT EXISTS ipsi_recommended_subjects (
  recommended_subject_id BIGINT NOT NULL AUTO_INCREMENT,
  university_id BIGINT NOT NULL,
  department_id BIGINT NULL,
  academic_year VARCHAR(10) NOT NULL,
  round_type VARCHAR(20) NULL COMMENT 'SUSI/JEONGSI(전체면 NULL)',
  subject_name VARCHAR(120) NOT NULL COMMENT '권장과목명',
  subject_type VARCHAR(40) NULL COMMENT '권장/필수/예시 등',
  source_document_id BIGINT NOT NULL,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (recommended_subject_id),
  KEY idx_ipsi_reco_lookup (university_id, academic_year),
  CONSTRAINT fk_ipsi_reco_univ FOREIGN KEY (university_id)
    REFERENCES ipsi_universities (university_id) ON DELETE CASCADE,
  CONSTRAINT fk_ipsi_reco_dept FOREIGN KEY (department_id)
    REFERENCES ipsi_departments (department_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='모집단위별 권장과목';
