package com.example.term_paper.repository

import com.example.term_paper.model.TestConfig
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface TestConfigsRepository : JpaRepository<TestConfig, Long> {
}