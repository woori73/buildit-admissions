-- BuildIt AI 입시상담 DB (1/4): 공식 출처 레지스트리 + 문서 + 문서 버전 (신규 테이블만, 기존 데이터 변경 없음)
--
-- 공통 AI 입시상담 Agent의 지식 DB 기반. 대학별 DB를 만들지 않고 하나의 검증된 입시 DB를 쓴다.
-- 설계 원칙(작업지시 2·3단계):
--  - 모든 레코드에 원문URL·기관명·문서명·발표일·적용학년도·수집일·검증상태를 남긴다.
--  - 자료 원본(raw_storage_key) / 구조화(structured_json) / 검색용 텍스트(search_text)를 분리 관리한다.
--  - 자료 변경 시 기존 기록을 삭제하지 않고 버전을 보존한다(ipsi_document_versions).
--  - 수집 즉시 상담DB 반영 금지: verification_status는 COLLECTED→EXTRACTED→NORMALIZED→REVIEW→APPROVED로만 승격.
--  - EBS 해설·전략 자료는 content_class=NON_OFFICIAL_RULE로 공식 전형규정과 구분한다.
--
-- 다음 마이그레이션 = V1065 (ipsi_universities / ipsi_departments)

CREATE TABLE IF NOT EXISTS ipsi_sources (
  source_id BIGINT NOT NULL AUTO_INCREMENT,
  source_key VARCHAR(60) NOT NULL COMMENT '출처 고유키(예: kcue, moe, ebsi)',
  institution_name VARCHAR(200) NOT NULL COMMENT '기관명',
  institution_type VARCHAR(30) NOT NULL COMMENT 'MINISTRY/COUNCIL/AGENCY/BROADCAST/UNIVERSITY',
  base_url VARCHAR(500) NULL,
  robots_our_ua_allowed TINYINT(1) NULL COMMENT '1=허용,0=차단,NULL=URL별 판정',
  robots_notes TEXT NULL COMMENT 'robots.txt 실측 근거',
  reuse_terms TEXT NULL COMMENT '이용약관·재이용 조건',
  redistribution VARCHAR(30) NOT NULL DEFAULT 'METADATA_PRIORITY' COMMENT 'OPEN/METADATA_PRIORITY/RESTRICTED',
  access_method VARCHAR(30) NOT NULL DEFAULT 'HTTP_STATIC' COMMENT 'HTTP_STATIC/JS_REQUIRED/METADATA_ONLY',
  content_class VARCHAR(30) NOT NULL DEFAULT 'OFFICIAL_RULE' COMMENT 'OFFICIAL_RULE/NON_OFFICIAL_RULE',
  collect_status VARCHAR(40) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (source_id),
  CONSTRAINT uq_ipsi_source_key UNIQUE (source_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='입시상담 공식 출처 레지스트리(기관·robots·이용조건·재배포 정책)';

CREATE TABLE IF NOT EXISTS ipsi_documents (
  document_id BIGINT NOT NULL AUTO_INCREMENT,
  source_id BIGINT NOT NULL,
  url_hash CHAR(64) NOT NULL COMMENT '정규 URL의 SHA-256(중복 방지)',
  original_url VARCHAR(1000) NOT NULL COMMENT '원문 URL',
  institution_name VARCHAR(200) NOT NULL COMMENT '기관명(스냅샷)',
  document_name VARCHAR(500) NOT NULL COMMENT '문서명',
  document_type VARCHAR(40) NOT NULL COMMENT 'PRESS_RELEASE/IMPLEMENTATION_PLAN/GUIDE_BOOK/MOE_CONFIRMED/ATTACHMENT/EXPLANATION',
  applicable_academic_year VARCHAR(10) NULL COMMENT '적용 학년도(예: 2028). NULL이면 상담검색 제외',
  published_at DATE NULL COMMENT '발표일',
  content_class VARCHAR(30) NOT NULL DEFAULT 'OFFICIAL_RULE' COMMENT '공식 전형규정 vs EBS 해설·전략 구분',
  current_version_id BIGINT NULL COMMENT '현재 버전(ipsi_document_versions.version_id, FK 미설정-순환방지)',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (document_id),
  CONSTRAINT uq_ipsi_document_url UNIQUE (url_hash),
  KEY idx_ipsi_document_source (source_id),
  KEY idx_ipsi_document_year (applicable_academic_year, content_class),
  CONSTRAINT fk_ipsi_document_source FOREIGN KEY (source_id)
    REFERENCES ipsi_sources (source_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='입시 문서(논리 단위). 버전은 ipsi_document_versions로 보존';

CREATE TABLE IF NOT EXISTS ipsi_document_versions (
  version_id BIGINT NOT NULL AUTO_INCREMENT,
  document_id BIGINT NOT NULL,
  version_no INT NOT NULL COMMENT '1부터 증가. 자료 변경 시 새 버전 추가(기존 보존)',
  content_hash CHAR(64) NOT NULL COMMENT '원문 SHA-256(변경 감지)',
  raw_storage_key VARCHAR(500) NULL COMMENT '원문 파일 저장키. 재배포 제한이면 NULL(메타+링크만)',
  raw_content_type VARCHAR(100) NULL,
  raw_size INT NULL,
  structured_json MEDIUMTEXT NULL COMMENT '구조화 데이터(JSON)',
  search_text MEDIUMTEXT NULL COMMENT '검색용 텍스트(원문과 분리 관리)',
  collected_at DATETIME(6) NOT NULL COMMENT '수집일',
  verification_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED' COMMENT 'COLLECTED/EXTRACTED/NORMALIZED/REVIEW/APPROVED',
  verified_by VARCHAR(50) NULL,
  change_note VARCHAR(500) NULL,
  created_at DATETIME(6) NULL,
  updated_at DATETIME(6) NULL,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  PRIMARY KEY (version_id),
  CONSTRAINT uq_ipsi_docver UNIQUE (document_id, version_no),
  KEY idx_ipsi_docver_status (verification_status),
  CONSTRAINT fk_ipsi_docver_document FOREIGN KEY (document_id)
    REFERENCES ipsi_documents (document_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='입시 문서 버전(원본/구조화/검색텍스트 분리 + 검증상태 + 변경이력 보존)';
