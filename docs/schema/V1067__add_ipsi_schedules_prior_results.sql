-- BuildIt AI 입시상담 DB (4/4): 전형 일정 + 전년도 경쟁률/입시결과 (신규 테이블만)
--
-- ipsi_schedules: 원서접수·서류·면접·실기·합격발표·등록 등 전형 일정.
-- ipsi_prior_results: 전년도 경쟁률·입시결과(충원·등록자 성적). 수치와 원문 문자열을 함께 보관한다.
-- 두 테이블 모두 공식 출처 문서 + 원문URL + 검증상태를 필수로 가진다.
--
-- 이 파일로 1차 입시 DB 스키마 완료. 다음 운영 마이그레이션 후보 = V1068.

CREATE TABLE IF NOT EXISTS ipsi_schedules (
  schedule_id BIGINT NOT NULL AUTO_INCREMENT,
  university_id BIGINT NULL COMMENT 'NULL=공통 일정(예: 대교협 공통원서 접수)',
  admission_type_id BIGINT NULL,
  academic_year VARCHAR(10) NOT NULL,
  round_type VARCHAR(20) NULL COMMENT 'SUSI/JEONGSI',
  event_name VARCHAR(160) NOT NULL COMMENT '원서접수/서류제출/면접/실기/합격발표/등록 등',
  starts_at DATE NULL,
  ends_at DATE NULL,
  schedule_text VARCHAR(500) NULL COMMENT '원문 그대로의 일정 문자열',
  source_document_id BIGINT NOT NULL,
  source_url VARCHAR(1000) NOT NULL,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (schedule_id),
  KEY idx_ipsi_schedule_lookup (academic_year, university_id, round_type),
  CONSTRAINT fk_ipsi_schedule_univ FOREIGN KEY (university_id)
    REFERENCES ipsi_universities (university_id) ON DELETE CASCADE,
  CONSTRAINT fk_ipsi_schedule_admtype FOREIGN KEY (admission_type_id)
    REFERENCES ipsi_admission_types (admission_type_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='전형 일정';

CREATE TABLE IF NOT EXISTS ipsi_prior_results (
  prior_result_id BIGINT NOT NULL AUTO_INCREMENT,
  university_id BIGINT NOT NULL,
  department_id BIGINT NULL,
  admission_type_id BIGINT NULL,
  academic_year VARCHAR(10) NOT NULL COMMENT '발표 기준 학년도',
  prior_academic_year VARCHAR(10) NULL COMMENT '실제 입시결과가 속한 학년도',
  round_type VARCHAR(20) NULL COMMENT 'SUSI/JEONGSI',
  result_type VARCHAR(40) NOT NULL COMMENT 'COMPETITION_RATE/ADMISSION_RESULT/GRADE/SCORE',
  applicant_count INT NULL COMMENT '지원자 수',
  admitted_count INT NULL COMMENT '모집/합격 인원',
  competition_rate DECIMAL(8,2) NULL COMMENT '경쟁률',
  grade_avg VARCHAR(40) NULL COMMENT '평균 등급(문자열)',
  score_avg VARCHAR(40) NULL COMMENT '평균 점수(문자열)',
  raw_value_text VARCHAR(200) NULL COMMENT '원문 수치 문자열(정규화 전 원본 보존)',
  source_document_id BIGINT NOT NULL,
  source_url VARCHAR(1000) NOT NULL,
  institution_name VARCHAR(200) NOT NULL,
  published_at DATE NULL,
  collected_at DATETIME(6) NOT NULL,
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (prior_result_id),
  KEY idx_ipsi_prior_lookup (university_id, academic_year, round_type),
  KEY idx_ipsi_prior_type (result_type, verification_status),
  CONSTRAINT fk_ipsi_prior_univ FOREIGN KEY (university_id)
    REFERENCES ipsi_universities (university_id) ON DELETE CASCADE,
  CONSTRAINT fk_ipsi_prior_dept FOREIGN KEY (department_id)
    REFERENCES ipsi_departments (department_id) ON DELETE SET NULL,
  CONSTRAINT fk_ipsi_prior_admtype FOREIGN KEY (admission_type_id)
    REFERENCES ipsi_admission_types (admission_type_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='전년도 경쟁률 및 입시결과';
