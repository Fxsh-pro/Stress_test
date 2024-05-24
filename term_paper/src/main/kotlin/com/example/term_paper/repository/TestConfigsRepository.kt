package com.example.term_paper.repository

import com.example.term_paper.model.TestConfig
import jakarta.persistence.LockModeType
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Lock
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface TestConfigsRepository : JpaRepository<TestConfig, Long> {

    // @Lock(LockModeType.PESSIMISTIC_READ)
    @Query("SELECT t FROM TestConfig t WHERE t.wasTested = 0")
    fun findAllNotTested(pageable: Pageable): List<TestConfig>
}