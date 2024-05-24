package com.example.term_paper.repository

import com.example.term_paper.model.StressTestResultModel
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository

@Repository
interface StressTestResultRepository : JpaRepository<StressTestResultModel, Long> {
    @Query("SELECT s.version FROM StressTestResultModel s WHERE s.testId = :testId ORDER BY s.version DESC LIMIT 1")
    fun findLatestByTestId(@Param("testId") testId: Int): Int?
}