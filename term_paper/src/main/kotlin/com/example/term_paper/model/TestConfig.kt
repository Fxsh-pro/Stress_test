package com.example.term_paper.model

import jakarta.persistence.Column
import jakarta.persistence.EnumType
import jakarta.persistence.Enumerated
import jakarta.persistence.FetchType
import jakarta.persistence.GeneratedValue
import jakarta.persistence.*
import jakarta.persistence.JoinColumn
import jakarta.persistence.TemporalType
import lombok.ToString
import java.util.Date
import kotlin.reflect.jvm.internal.impl.builtins.functions.FunctionInvokeDescriptor.Factory

@Entity
@Table(name = "test_configs")
class TestConfig {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    var id: Int = 0

    @Column(name = "endpoint", nullable = false, length = 255)
    var endpoint: String = ""

    @Column(name = "request_body", columnDefinition = "text")
    var requestBody: String? = null

    @Enumerated(EnumType.STRING)
    @Column(name = "method", nullable = false)
    var method: HttpMethod? = null

    @Column(name = "request_arguments", columnDefinition = "text")
    var requestArguments: String? = null

    @Column(name = "count_of_tests", nullable = false)
    var countOfTests: Int = 0

    @Column(name = "headers", columnDefinition = "text")
    var headers: String? = null

    @Column(name = "user_id")
    var user_id: Int? = null

    @Column(name = "created_at", columnDefinition = "datetime default CURRENT_TIMESTAMP", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    var createdAt: Date = Date()

    @Column(name = "was_tested")
    var wasTested: Int = 0

    override fun toString(): String {
        return "TestConfig(id=$id, endpoint='$endpoint', method=$method, user_id=$user_id)"
    }
}

