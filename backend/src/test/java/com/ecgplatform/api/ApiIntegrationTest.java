package com.ecgplatform.api;

import com.ecgplatform.api.service.ClassifierService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ApiIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ClassifierService classifierService;

    @Test
    void healthReturnsOkWhenClassifierUp() throws Exception {
        when(classifierService.isHealthy()).thenReturn(true);

        mockMvc.perform(get("/api/v1/health"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.classifier").value("up"));
    }

    @Test
    void healthReturnsDegradedWhenClassifierDown() throws Exception {
        when(classifierService.isHealthy()).thenReturn(false);

        mockMvc.perform(get("/api/v1/health"))
            .andExpect(status().isServiceUnavailable())
            .andExpect(jsonPath("$.status").value("degraded"))
            .andExpect(jsonPath("$.classifier").value("down"));
    }

    @Test
    void registerCreatesUserAndReturnsToken() throws Exception {
        String email = "test-" + UUID.randomUUID() + "@example.com";
        String body = """
            {"email":"%s","password":"password123"}
            """.formatted(email);

        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(body))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.token").isNotEmpty())
            .andExpect(jsonPath("$.email").value(email));
    }

    @Test
    void protectedRouteRequiresAuth() throws Exception {
        mockMvc.perform(get("/api/v1/ecg"))
            .andExpect(status().isForbidden());
    }
}
