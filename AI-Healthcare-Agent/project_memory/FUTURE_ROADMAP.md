# Future Roadmap

> Development milestones organized by version.
> Updated as priorities evolve.

---

## MVP (v1.0.0) — Current Target

**Estimated Completion:** Q3 2026

### Required for MVP Launch
- [x] Authentication (Register, Login, Logout, Refresh, RBAC)
- [x] Database migrations + seed data
- [ ] OCR file upload (PDF/Image → text)
- [ ] Medical Report Agent (extract medicines from prescriptions)
- [ ] Patient Chat Agent (RAG over patient reports)
- [ ] Medicine Reminder Agent (schedules + adherence tracking)
- [ ] Emergency Detection Agent (symptom triage)
- [ ] Doctor Summary Agent (patient summaries)
- [ ] Doctor Dashboard (patient list, adherence view, alert management)
- [ ] Docker deployment (Vercel + Render + Neon)

### MVP Success Criteria
- Patient can register, upload prescription, see extracted medicines, chat about them
- Doctor can login, see assigned patients, view summaries, acknowledge alerts
- System tracks adherence, sends reminders, detects emergencies
- All flows work end-to-end in production

---

## Version 1.1

**Estimated:** 2-4 weeks after MVP

### Planned Features
- **Email notifications** — Twilio SendGrid for password reset, appointment reminders
- **Password reset flow** — Forgot password → email → reset
- **Rate limiting** — Redis-backed rate limiting on auth endpoints
- **Error monitoring** — Sentry integration for production error tracking
- **Loading skeletons** — Better UX for dashboard loading states
- **Pagination** — For reports, chat history, appointment lists
- **Database indexes** — Performance optimization for common queries
- **Refresh token cleanup** — Scheduled job to remove expired tokens

---

## Version 2.0

**Estimated:** Q4 2026

### Major Features
- **Admin dashboard** — User management, system analytics, configuration
- **SMS notifications** — Twilio SMS for medicine reminders and alerts
- **Push notifications** — Web Push API for in-app reminders
- **Multi-language support** — i18n for English + additional languages
- **Appointment scheduling** — Calendar integration, auto-reminders
- **Advanced analytics** — Adherence trends, population health insights
- **Report comparison** — Compare multiple reports over time

### Improvements
- RS256 JWT signing for microservice readiness
- WebSocket-based real-time chat
- Agent response streaming
- Improved RAG with hybrid search

---

## Version 3.0

**Estimated:** Q1 2027

### Major Features
- **WhatsApp chatbot** — Patient interaction via WhatsApp
- **EHR integration** — FHIR standard for hospital system compatibility
- **Video consultation** — Real-time video with WebRTC
- **Offline mode** — Service worker + IndexedDB for offline access
- **Mobile apps** — React Native for iOS and Android

### Improvements
- Full HIPAA compliance readiness
- SOC 2 compliance
- Multi-tenant architecture support
- White-labeling for hospital partners

---

## Long-term Startup Vision

### Value Proposition
- Reduce hospital readmission rates by 30% through proactive monitoring
- Increase medication adherence from ~50% to >80%
- Reduce doctor administrative time by 40% through AI summaries
- Provide early warning system for post-discharge complications

### Revenue Opportunities
1. **SaaS subscription** — Monthly per-patient fee to hospitals
2. **Enterprise tier** — Custom integrations, dedicated support, SLA
3. **White-label** — Hospital-branded versions of the platform
4. **API access** — Allow third-party integration with patient consent
5. **Data insights** — Anonymized population health analytics (with consent)

### Scalability Plan
- **Phase 1:** Single-tenant, single-region (current)
- **Phase 2:** Multi-tenant with tenant isolation
- **Phase 3:** Multi-region with CDN and read replicas
- **Phase 4:** Microservices split (auth, chat, agents, notifications)
- **Phase 5:** Global with edge functions and distributed database

### Potential Integrations
- **EHR Systems:** Epic, Cerner, Athenahealth (via FHIR)
- **Pharmacy:** PillPack, Amazon Pharmacy (via API)
- **Wearables:** Apple Health, Fitbit, Google Fit (via Health Connect)
- **Telehealth:** Zoom, Doximity, Teladoc (via API)
- **Insurance:** Prior authorization, claims data (via clearinghouse)

### Future AI Features
- **Predictive analytics** — Predict readmission risk using patient history
- **Personalized recommendations** — Suggest lifestyle changes based on conditions
- **Drug interaction detection** — Flag dangerous combinations
- **Voice interface** — Voice-based symptom reporting and chat
- **Multimodal AI** — Process images, voice, text together
- **Federated learning** — Train models across hospitals without sharing patient data
- **Explainable AI** — Provide reasoning for all AI decisions for clinical trust
