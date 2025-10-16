
USE PortManager;

-- 1) Portfolios
CREATE TABLE portfolios (
  portfolio_id       INT AUTO_INCREMENT PRIMARY KEY,
  name               VARCHAR(200) NOT NULL,
  interpretation_text TEXT NULL,
  avg_irr_actual     DECIMAL(6,4) NULL,
  avg_irr_target     DECIMAL(6,4) NULL,
  avg_dscr           DECIMAL(6,4) NULL,
  avg_ltv            DECIMAL(6,4) NULL,
  total_equity       DECIMAL(15,2) NULL,
  total_value        DECIMAL(15,2) NULL,
  total_debt         DECIMAL(15,2) NULL,
  variance_irr       DECIMAL(6,4) NULL,
  variance_noi       DECIMAL(8,4) NULL,
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2) Properties (OWNED only)
CREATE TABLE properties (
  property_id           INT AUTO_INCREMENT PRIMARY KEY,
  portfolio_id          INT NOT NULL,
  name                  VARCHAR(200) NOT NULL,
  address               VARCHAR(300) NOT NULL,
  city                  VARCHAR(120) NULL,
  state                 VARCHAR(80) NULL,
  zip                   VARCHAR(20) NULL,

  -- Current (“actual”) snapshot fields (simple for MVP)
  current_value         DECIMAL(15,2) NULL,
  current_rent          DECIMAL(12,2) NULL,
  current_expense       DECIMAL(12,2) NULL,
  vacancy_rate          DECIMAL(5,4) NULL,
  capex_spent           DECIMAL(12,2) NULL,
  tax_expense_annual    DECIMAL(12,2) NULL,

  -- Loan snapshot
  loan_balance          DECIMAL(15,2) NULL,
  loan_rate             DECIMAL(6,4) NULL,
  loan_amort_years      INT NULL,
  loan_interest_paid_td DECIMAL(15,2) NULL,
  loan_principal_paid_td DECIMAL(15,2) NULL,

  acquisition_date      DATE NULL,
  snapshot_date         DATE NULL, -- today’s date at input time
  notes                 TEXT NULL,

  CONSTRAINT fk_properties_portfolio
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3) Pro forma (underwriting at acquisition; 1:1 with property)
CREATE TABLE proforma_data (
  proforma_id        INT AUTO_INCREMENT PRIMARY KEY,
  property_id        INT NOT NULL UNIQUE, -- 1:1
  purchase_price     DECIMAL(15,2) NOT NULL,
  expected_rent      DECIMAL(12,2) NULL,
  expected_expenses  DECIMAL(12,2) NULL,
  expected_noi       DECIMAL(12,2) NULL,
  capex_budget       DECIMAL(12,2) NULL,
  ltv                DECIMAL(6,4) NULL,
  loan_rate          DECIMAL(6,4) NULL,
  amort_years        INT NULL,
  io_years           INT NULL,
  target_irr         DECIMAL(6,4) NULL,
  target_coc         DECIMAL(6,4) NULL,
  exit_cap_rate      DECIMAL(6,4) NULL,
  cashflow_file_path VARCHAR(400) NULL, -- path to Excel/CSV
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_proforma_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4) Market data snapshot (context linked to property)
CREATE TABLE market_data (
  market_id           INT AUTO_INCREMENT PRIMARY KEY,
  property_id         INT NOT NULL,
  region_code         VARCHAR(40) NULL, -- e.g., ZIP / MSA code
  rent_growth_yoy     DECIMAL(6,4) NULL,
  vacancy_rate_market DECIMAL(6,4) NULL,
  cap_rate_market     DECIMAL(6,4) NULL,
  interest_rate_10yr  DECIMAL(6,4) NULL,
  employment_growth   DECIMAL(6,4) NULL,
  population_growth   DECIMAL(6,4) NULL,
  risk_score          DECIMAL(6,4) NULL, -- your composite 0–1
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_market_property (property_id),
  CONSTRAINT fk_market_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5) AI Suggestions (actions per property; keep history)
CREATE TABLE suggestions (
  suggestion_id        INT AUTO_INCREMENT PRIMARY KEY,
  property_id          INT NOT NULL,
  action               ENUM('sell','refinance','hold') NOT NULL,
  confidence_score     DECIMAL(6,4) NULL,
  rationale_portfolio  TEXT NULL,
  rationale_market     TEXT NULL,
  rationale_performance TEXT NULL,
  ai_summary           TEXT NULL,
  created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_suggestions_property (property_id),
  CONSTRAINT fk_suggestions_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6) Potential properties (pipeline) — minimal, recalculated live
CREATE TABLE potential_properties (
  potential_id          INT AUTO_INCREMENT PRIMARY KEY,
  portfolio_id          INT NOT NULL,
  name                  VARCHAR(200) NOT NULL,
  address               VARCHAR(300) NULL,
  city                  VARCHAR(120) NULL,
  state                 VARCHAR(80) NULL,
  zip                   VARCHAR(20) NULL,

  -- Minimal assumptions only (no stored pro formas/market)
  purchase_price_assumed DECIMAL(15,2) NULL,
  rent_assumed           DECIMAL(12,2) NULL,
  expenses_assumed       DECIMAL(12,2) NULL,
  loan_rate_assumed      DECIMAL(6,4) NULL,
  ltv_assumed            DECIMAL(6,4) NULL,
  hold_years_assumed     DECIMAL(6,2) NULL,
  sale_price_assumed     DECIMAL(15,2) NULL,

  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_potential_portfolio (portfolio_id),
  CONSTRAINT fk_potential_portfolio
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
