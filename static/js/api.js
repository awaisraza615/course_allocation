
const API_BASE_URL = "";

async function apiRequest(endpoint, options = {}) {
    const config = {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    };

    try {
        const response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            config
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.detail || "Something went wrong"
            );
        }

        return data;

    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

export const api = {
    get(endpoint) {
        return apiRequest(endpoint);
    },

    post(endpoint, body) {
        return apiRequest(endpoint, {
            method: "POST",
            body: JSON.stringify(body)
        });
    },

    put(endpoint, body) {
        return apiRequest(endpoint, {
            method: "PUT",
            body: JSON.stringify(body)
        });
    },

    patch(endpoint, body) {
        return apiRequest(endpoint, {
            method: "PATCH",
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return apiRequest(endpoint, {
            method: "DELETE"
        });
    }
};
