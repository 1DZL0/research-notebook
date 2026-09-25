Work package WP3 – AI and Data Tools and Services
Work Package Number WP3 Lead Beneficiary 1 - CYI
Work Package Name AI and Data Tools and Services
Start Month 1 End Month 36
Objectives
Work Package 3 (WP3) aims to establish the technical foundation and service ecosystem that will support trustworthy,
efficient, and policy-aligned AI development within Pharos-CY. It focuses on enabling secure access to data, scalable
AI workflows, and compliance with European regulatory frameworks such as the EU AI Act and the Data Governance
Act. WP3 will develop modular tools and services that support the full AI lifecycle – from data processing and model
training to deployment and monitoring – while ensuring interoperability with DAEDALUS of the Greek AI Factory. It
will also provide secure digital environments for sensitive data handling and promote responsible AI practices through
self-assessment frameworks and regulatory guidance. Additionally, WP3 will coordinate the setup and operation of the
underlying infrastructure needed to support these services across participating institutions.
Description
Task 3.1: Tools and services for trustworthy and efficient ML training, fine-tuning and inference, M01 – M36, Lead:
CaSToRC (CYI), Participants: CING, CYENS, CUT, KIOS (UCY) and UCY.
Task 3.1 (T3.1) will provide a modular, end-to-end toolkit that guides users through every stage of machine learning
(ML) model development, embedding the principles of Trustworthy AI in alignment with the EU AI Act. The
environment will include preconfigured, containerized workspaces based on widely used frameworks such as PyTorch
and TensorFlow, with seamless access to both local AI-optimized infrastructure and EuroHPC JU compute resources.
The task revolves around the Pharos-CY AI Registry, which will provide curated, FAIR-compliant datasets and pretrained models across key domains, including NLP (e.g., BERT, LLaMA 3), computer vision (e.g., ResNet, Vision
Transformer), and multimodal applications (e.g., SAM, OpenCLIP, OWL-ViT), served via MLflow Model Registry,
Kubeflow with KServe, and Hugging Face Private Hub. Users can leverage automated pipelines for data preprocessing,
model sparsification, hyperparameter tuning, and distributed training – augmented by an in-development Conformity
Assessment and Ethics Self-Assessment. To ensure high-quality and reproducible AI workflows, the environment will
10
Associated with document Ref. Ares(2026)3420075 - 31/03/2026
Project: 101263007 — Pharos-CY — HORIZON-JU-EUROHPC-2025-AIFA-01
integrate tools such as pandas, scikit-learn, and TensorFlow Transform for data cleaning and transformation, alongside
torchvision and AugLy for augmentation of visual, text, and audio data. Federated Learning (FL) frameworks (e.g.,
Flower) will also be introduced, enabling users to train models not only on data available within Pharos, but also by
leveraging data residing on other infrastructures or AI Factories across Europe. Hyperparameter optimization will be
enabled through Optuna and Ray Tune, while containerization using Docker or Singularity will ensure portability and
consistency across different systems. Robust tooling for experiment tracking, model versioning, and deployment will
be provided through MLflow, DVC, and ClearML, with CI/CD workflows managed via Apache Airflow, ZenML, and
BentoML, and automation frameworks such as GitLab CI, Jenkins, and Argo Workflows. Deployed models will be
continuously monitored using MLWatch, Evidently, Deepchecks, and Langtrace, while infrastructure-level observability
supported by Prometheus and Grafana. Integrated explainability and bias detection tools will further support the
development of responsible AI systems. The task will also support regulatory alignment through the implementation
of conformity and ethics self-assessment workflows, CE marking, and post-deployment surveillance as required by the
AI Act. This task will be led by CYI (CaSToRC), which will coordinate contributions from CING, CYENS, CUT,
and KIOS (UCY) and CS (UCY), with responsibilities allocated according to the thematic and technical focus of each
contributing institution. To support reproducibility, the task will include a sandboxed emulator that simulates AI model
behavior across different deployment scenarios and risk levels. This allows users to test and validate model performance,
robustness, and bias before deploying in real-world settings.
Task 3.2: Algorithmic Support for AI applications in HPC environments, M03 – M36, Lead: CaSToRC (CYI),
Participants: CING, CYENS, CYNET, KIOS (UCY) and UCY.
Τask 3.2 (T3.2) will tailor AI development workflows for execution on the HPC system, DAEDALUS. A unified
interface will facilitate seamless access to compute resources, ranging from single-GPU workstations to multi-node
clusters, using role-based, secure access. AI workloads will be encapsulated in containerized pipelines orchestrated
via Kubernetes, Kubeflow, or Apache Airflow, enabling portability and scalable deployment. To boost autonomy and
efficiency, intelligent AI agents will be embedded in the orchestration layer to manage resources,schedule jobs, and adapt
workflows in real time. These agents operate using declarative goals and learn from past performance to optimize tasks
like data processing, model training, and deployment across workflows. The system will support workload submission
through web interfaces, command-line tools, or APIs. Real-time GPU and CPU usage will be monitored through
integrated dashboards, and identity management will be handled through federated authentication mechanisms such as
eduGAIN. Best practice guidelines will be provided for efficient parallelization, memory optimization, and resource
utilization, leveraging tools such as Horovod, PyTorch Distributed Data Parallel, and Ray.
Task 3.3: Access to data sources and common European Data Spaces, M03 – M36, Lead: KIOS (UCY), Participants:
CaSToRC (CYI), CING, CYENS, CYNET and ECoE.
This task (T3.3) will establish technical and administrative mechanisms for authorized access to data infrastructures,
including cloud storage and secure research networks. It will leverage a vast array of datasets from key sectors aligned
with Pharos-CY – Health, Culture and Language, and Sustainability provided by public bodies such as the Statistical
Service, Ministry of Health, and Ministry of Agriculture, Rural Development and Environment, as well as domainspecific datasetsfrom project partners(see Table 3,Section 2.2.1 of application form). These sectors align closely with the
key industrial sectors ofPharos.Since not all datasets are AI-ready, a core focus will be enhancing their usability through
curation, structuring, and semantic annotation. Pharos-CY will ensure proper indexing and documentation, applying
metadata standards aligned with FAIR principles. The project will also connect to selected European Data Spaces – such
as those for Energy, the Green Deal, Health, and Language – via federation with EOSC and other cross-border initiatives.
This includes implementing APIs, authentication and authorization (AAI), and middleware to support data discovery,
sharing, and semantic interoperability. Access protocols will align with data governance frameworks promoted by GAIAX and related platforms.
Task 3.4: Establishment of secure and trusted environments, M03 – M36, Lead: CYNET, Participants: CaSToRC (CYI),
CYENS, KIOS (UCY) and UCY.
Task 3.4 (T3.4), led by CYNET with contributionsfrom CaSToRC (CYI), CYENS, KIOS(UCY) and CS(UCY), focuses
on designing and deploying secure, policy-compliant digital environments to support responsible AI development and
sensitive data processing across domains such as healthcare, genomics, and public services. A federated trust and security
architecture will be implemented across Pharos-CY institutions, incorporating encrypted storage, secure virtualization,
real-time auditing, and fine-grained access controls. Federated identity and authentication mechanisms, aligned with
eduGAIN, will enable seamless and secure access for users via institutional credentials, supporting both role-based and
attribute-based access control. These environments will be integrated with CYNET’s national infrastructure, including a
100 Gbps backbone and enterprise-grade cybersecurity systems. The task will also define compliance frameworks, risk
mitigation protocols, and onboarding procedures for sensitive data. Designed for interoperability with EOSC, Gaia-X,
and EuroHPC JU, the resulting infrastructure will ensure full alignment with European legal, ethical, and cybersecurity
standards, creating a trusted and scalable ecosystem for AI innovation.




Work package WP7 – Training and Development
Work Package Number WP7 Lead Beneficiary 4 - UCY
Work Package Name Training and Development
Start Month 1 End Month 36
Objectives
The objectives of WP7 are to address AI skill gaps through a coordinated set of training and development activities. It will
begin with the analysis of national training needs and the planning of relevant activities, followed by the establishment
of the Pharos-CY Training Hub, a central coordination point for all AI training and development activities. WP7 will
develop modular training programs for reskilling and upskilling, as well as hands-on training events, such as, workshops,
hackathons, and summer schools. WP7 will also foster collaboration with universities and with national and European
initiatives, such as, the European Digital Innovation Hubs (EDIHs) and National Competence Centers, thus facilitating
the long-term sustainability and integration into talent ecosystems.
Description
Task 7.1: Analysis of needs for AI skills in Cyprus and planning of activities, M01 – M12, Lead: KIOS (UCY),
Participants: CaSToRC (CYI), CING and CYENS.
This task (T7.1) will identify current gaps in the AI landscape of the country, as well as skillsets across stakeholders
in academia, public sectors, and industry. Pharos-CY will conduct requirements collection/needs analysis via various
media, such as stakeholder consultations, targeted surveys, questionnaires, and by reviewing the national and European
digital skills strategies. The focus will be on the thematic domains aligned with Pharos. These are Health, Sustainability,
and Culture & Language. Based on the findings of this analysis, which will be presented in D7.1, a strategic training
plan will be developed, with identified target groups, and types of training programs needed for reskilling and upskilling.
This plan will form the basis for the design and implementation of the training programs in the tasks that follow.
Task 7.2: Development and coordination of the Pharos-CY training hub, M01 – M36, Lead: KIOS (UCY), Participants:
CaSToRC (CYI), CING and CYENS.
This task (T7.2) will establish the Pharos-CY’s Training Hub, which will serve as the central coordination point for all
AI training and development activities. The hub will be setup as a “virtual, distributed office” across the Core Partners
involved, with clear roles defined to ensure smooth collaboration. A dedicated training coordinator will be appointed to
manage the Hub’s operations, including, to liaise with stakeholders, maintain visibility, and oversee logistics. PharosCY Training Hub will be responsible for organising the various types of training programs (e.g., short courses and
specializations) and hands-on training events (e.g., workshops, hackathons and summer schools), as well as responsible
for maintaining a repository of the training material. Importantly, to maximise impact, accessibility and visibility, an
outreach plan will be launched to promote the hub to prospective stakeholders. The Pharos-CY Training Hub will work
in close collaboration with the Pharos WP5 “Building Training Capacity and Skills”, exploring the co-organization of
training events and the exchange of training materials and expertise. Coordination of joint activities between the two
projects will be managed by the training coordinator. In addition, T7.2 will establish a dedicated task force to develop and
propose recommendations to the Ministry of Education for enhancing the current Information Technology curricula in
high schools. This initiative will be carried out in close collaboration with Ministry personnel and the project GenAI4ED,
19
Associated with document Ref. Ares(2026)3420075 - 31/03/2026
Project: 101263007 — Pharos-CY — HORIZON-JU-EUROHPC-2025-AIFA-01
building on the relationships and channels of communication already established through the EuroCC2 and DiGiNN
(EDIH) projects.
Task 7.3: Development of modular training programs for reskilling and upskilling, M01 – M36, Lead: CaSToRC (CYI),
Participants: CING, CYENS, KIOS (UCY), UCY and CUT.
This task (T7.3) focuses on the design and implementation of comprehensive training programs that provide targeted
reskilling and upskilling opportunities across diverse sectors. The programs will serve three key audiences: (a) career
transitioners seeking to enter AI-related roles or industries, (b) current employees requiring enhanced skills to effectively
integrate AI technologies into their work, and (c) students, early-career researchers beginning their AI journey. The
training system will include hands-on experience with data analysis, ML, and the practical use of AI tools and LLMs.
These programs will be customized to addressthe specific needs and challenges of targeted audience and will be delivered
in both in-person and online formats. HPC resources will be integrated into the training infrastructure to support advanced
learning and experimentation.Furthermore,Pharos-CY will leverage existing academic offerings provided by university
partners. These include selected modules from established postgraduate programs, specifically, CUT’s MSc in AI and
Data Engineering, UCY’s MSc in AI (e.g. machine / deep learning), MSc in Data Science (e.g. big data / business
analytics), and MSc in Cognitive Systems (e.g. computational neuroscience). Additionally, Pharos-CY partners will
collaborate closely with the UCY for the development of micro-credentials of training programs to appeal more widely
to the target audience.
Task 7.4: Collaboration with universities, M01 – M36, Lead: KIOS (UCY), Participants: CaSToRC (CYI), CING,
CYENS, UCY and CUT.
Task 7.4 (T7.4) will focus on establishing new (or strengthening existing) collaborations with universities to support
long-term capacity building in AI. Pharos-CY will work closely with academic institutions to jointly develop and deliver
new AI training courses that complement existing offerings.Furthermore,Pharos-CY partners will deliver guest lectures
within existing university programs (such as MSc in Data Science and AI degrees). These lectures aim to introduce
students to Pharos-CY, to help form strong links between Pharos-CY and the academic community, and to showcase
successful applications of AI in the areas of Health, Sustainability as well as in culture and language. To further enhance
collaboration, the task will also establish internship programs, enabling students to gain practical experience with AI
startups and companies. Overall, these collaborations will enhance the visibility, relevance, and long-term impact of
Pharos-CY’s training activities.
