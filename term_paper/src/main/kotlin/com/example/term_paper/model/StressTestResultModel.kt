package com.example.term_paper.model

import jakarta.persistence.Column
import jakarta.persistence.EnumType
import jakarta.persistence.Enumerated
import jakarta.persistence.FetchType
import jakarta.persistence.GeneratedValue
import jakarta.persistence.*
import jakarta.persistence.JoinColumn
import jakarta.persistence.TemporalType
import lombok.AllArgsConstructor
import lombok.Builder
import lombok.Data
import lombok.NoArgsConstructor
import lombok.ToString
import java.time.Instant
import java.util.Date

@Entity
@Table(name = "test_results")
@Data
class StressTestResultModel {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Int = 0

    @Column(name = "test_id", nullable = false)
    var testId: Int = 0

    @Column(name = "start_time", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    var startTime: Instant = Instant.now()

    @Column(name = "end_time", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    var endTime: Instant  = Instant.now()

    @Column(name = "metrics", columnDefinition = "json", nullable = false)
    var metrics: String = ""

    @Column(name = "version", nullable = false)
    var version: Int = 0

    override fun toString(): String {
        return "TestResult(id=$id, testId=$testId, startTime=$startTime, endTime=$endTime, metrics='$metrics', version=$version)"
    }
}