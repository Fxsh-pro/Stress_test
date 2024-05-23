package com.example.term_paper

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.scheduling.annotation.EnableScheduling

@SpringBootApplication
@EnableScheduling
class TermPaperApplication

fun main(args: Array<String>) {
    runApplication<TermPaperApplication>(*args)
}
