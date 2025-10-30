
-- Use the database
USE portfolio_mgr;

-- ==========================================
-- 1) Portfolios
-- ==========================================
CREATE TABLE portfolios (
  portfolio_id        INT AUTO_INCREMENT PRIMARY KEY,
  name                VARCHAR(200) NOT NULL UNIQUE,
  interpretation_text TEXT NULL,
  avg_irr_actual      DECIMAL(6,4) NULL,
  avg_irr_target      DECIMAL(6,4) NULL,
  avg_dscr            DECIMAL(6,4) NULL,
  avg_ltv             DECIMAL(6,4) NULL,
  total_equity        DECIMAL(15,2) NULL,
  total_value         DECIMAL(15,2) NULL,
  total_debt          DECIMAL(15,2) NULL,
  variance_irr        DECIMAL(6,4) NULL,
  variance_noi        DECIMAL(8,4) NULL,
  last_updated        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ==========================================
-- 2) Properties (Manual Input + Basic API Data)
-- ==========================================
CREATE TABLE properties (
  property_id            INT AUTO_INCREMENT PRIMARY KEY,
  portfolio_id           INT NOT NULL,
  name                   VARCHAR(200) NOT NULL,
  address                VARCHAR(300) NOT NULL,
  city                   VARCHAR(120) NULL,
  state                  VARCHAR(80) NULL,
  zip                    VARCHAR(20) NULL,

  -- Property Characteristics (Manual Input)
  property_type          ENUM('Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Land', 'Manufactured') NULL,
  bedrooms               INT NULL,
  bathrooms              DECIMAL(3,1) NULL,
  year_built             INT NULL,
  property_sf            INT NULL,

  -- Current State (Manual Input - User provides)
  current_value          DECIMAL(15,2) NULL,           -- User input
  current_rent           DECIMAL(12,2) NULL,           -- User input
  current_expense        DECIMAL(12,2) NULL,           -- User input
  current_vacancy_rate   DECIMAL(5,4) NULL,            -- User input
  current_tax_annual     DECIMAL(12,2) NULL,           -- User input

  -- Current Loan State (Manual Input - User provides)
  current_loan_balance   DECIMAL(15,2) NULL,
  current_loan_rate      DECIMAL(6,4) NULL,
  current_loan_remaining_years INT NULL,

  -- Timestamps
  acquisition_date       DATE NULL,
  last_updated           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  notes                  TEXT NULL,

  CONSTRAINT fk_properties_portfolio
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==========================================
-- 3) Acquisition Data (Manual Input)
-- ==========================================
CREATE TABLE acquisition_data (
  acquisition_id        INT AUTO_INCREMENT PRIMARY KEY,
  property_id           INT NOT NULL UNIQUE,
  
  -- Manual Input Fields (your complete list)
  purchase_price        DECIMAL(15,2) NOT NULL,
  closing_costs         DECIMAL(12,2) NULL,
  date_of_close         DATE NOT NULL,
  property_sf           INT NOT NULL,
  
  -- Income at Acquisition
  rent_immediately_after_purchase DECIMAL(12,2) NULL,
  vacancy_immediately_after_purchase DECIMAL(5,4) NULL,
  other_income_immediately_after_purchase DECIMAL(12,2) NULL,
  
  -- Expenses at Acquisition
  operating_expenses_after_purchase DECIMAL(12,2) NULL,
  capital_expense_after_purchase DECIMAL(12,2) NULL,
  tax_assessment_price_immediately_after_purchase DECIMAL(15,2) NULL,
  capital_expenses_right_after_purchase DECIMAL(12,2) NULL,
  
  -- Exit Assumptions
  exit_cap_rate_expectation DECIMAL(6,4) NULL,
  hold_period_years     INT NULL,
  cost_of_sale_percentage DECIMAL(5,4) NULL,
  
  -- Loan at Acquisition
  ltv                   DECIMAL(6,4) NULL,
  loan_origination_fee  DECIMAL(6,4) NULL,
  interest_rate         DECIMAL(6,4) NULL,
  amortization_years    INT NULL,
  
  -- Growth Assumptions
  expected_rent_growth  DECIMAL(6,4) NULL,
  expected_expense_growth DECIMAL(6,4) NULL,
  expected_capex_growth DECIMAL(6,4) NULL,
  expected_appreciation DECIMAL(6,4) NULL,
  
  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_acquisition_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==========================================
-- 4) Proforma Data (calc_engine output)
-- ==========================================
CREATE TABLE proforma_data (
  proforma_id           INT AUTO_INCREMENT PRIMARY KEY,
  property_id           INT NOT NULL UNIQUE,

  -- Acquisition / Going-In Metrics
  going_in_cap_rate     DECIMAL(6,4),
  loan_constant         DECIMAL(6,4),
  going_in_dscr         DECIMAL(6,4),
  going_in_debt_yield   DECIMAL(6,4),

  -- Unlevered Performance
  unlevered_irr         DECIMAL(6,4),
  avg_unlevered_coc     DECIMAL(6,4),
  unlevered_equity_multiple DECIMAL(6,4),

  -- Levered Performance
  levered_irr           DECIMAL(6,4),
  avg_levered_coc       DECIMAL(6,4),
  levered_equity_multiple DECIMAL(6,4),

  -- Exit Metrics
  exit_ltv              DECIMAL(6,4),
  year1_op_ex_ratio     DECIMAL(6,4),
  projected_sale_price  DECIMAL(15,2),
  net_sale_proceeds     DECIMAL(15,2),

  -- Projection Period
  projection_start_date DATE NULL,
  projection_end_date   DATE NULL,
  months_projected      INT NULL,

  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_proforma_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;


-- ==========================================
-- 5) Market Data (RentCast + FRED APIs)
-- ==========================================
CREATE TABLE market_data (
  market_id            INT AUTO_INCREMENT PRIMARY KEY,
  property_id          INT NOT NULL,
  region_code          VARCHAR(40) NULL,
  
  -- Market Trends (from APIs)
  rent_growth_yoy      DECIMAL(6,4) NULL,           -- From RentCast historical data
  vacancy_rate_market  DECIMAL(6,4) NULL,           -- From FRED
  cap_rate_market      DECIMAL(6,4) NULL,           -- From FRED (10-year Treasury + spread)
  interest_rate_10yr   DECIMAL(6,4) NULL,           -- From FRED
  employment_growth    DECIMAL(6,4) NULL,           -- From FRED
  population_growth    DECIMAL(6,4) NULL,           -- From FRED
  
  -- Market Comps (from RentCast)
  median_rent          DECIMAL(12,2) NULL,           -- From RentCast
  median_price_per_sf  DECIMAL(12,2) NULL,           -- From RentCast
  median_price         DECIMAL(15,2) NULL,           -- From RentCast
  
  -- Property Type Specific Comps (from RentCast)
  comp_rent_sf         DECIMAL(8,4) NULL,            -- Rent per sq ft for property type
  comp_price_sf        DECIMAL(8,4) NULL,            -- Price per sq ft for property type
  
  -- Risk Assessment
  risk_score           DECIMAL(6,4) NULL,
  
  updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_market_property (property_id),
  CONSTRAINT fk_market_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==========================================
-- 6) AI Suggestions (3-Tier Analysis Results)
-- ==========================================
CREATE TABLE suggestions (
  suggestion_id         INT AUTO_INCREMENT PRIMARY KEY,
  property_id           INT NOT NULL,
  
  -- Recommendation
  action                ENUM('sell','refinance','hold') NOT NULL,
  confidence_score      DECIMAL(6,4) NULL,
  
  -- 3-Tier Analysis Rationale
  rationale_level1     TEXT NULL,                   -- Property vs. Proforma
  rationale_level2     TEXT NULL,                   -- Property vs. Market
  rationale_level3     TEXT NULL,                   -- Property vs. Portfolio
  
  -- AI Summary
  ai_summary            TEXT NULL,
  
  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_suggestions_property (property_id),
  CONSTRAINT fk_suggestions_property
    FOREIGN KEY (property_id) REFERENCES properties (property_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==========================================
-- 7) Potential Properties (pipeline)
-- ==========================================
CREATE TABLE potential_properties (
  potential_id           INT AUTO_INCREMENT PRIMARY KEY,
  portfolio_id           INT NOT NULL,
  name                   VARCHAR(200) NOT NULL,
  address                VARCHAR(300) NULL,
  city                   VARCHAR(120) NULL,
  state                  VARCHAR(80) NULL,
  zip                    VARCHAR(20) NULL,

  purchase_price_assumed DECIMAL(15,2) NULL,
  rent_assumed           DECIMAL(12,2) NULL,
  expenses_assumed       DECIMAL(12,2) NULL,
  loan_rate_assumed      DECIMAL(6,4) NULL,
  ltv_assumed            DECIMAL(6,4) NULL,
  hold_years_assumed     DECIMAL(6,2) NULL,
  sale_price_assumed     DECIMAL(15,2) NULL,

  created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_potential_portfolio (portfolio_id),
  CONSTRAINT fk_potential_portfolio
    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
