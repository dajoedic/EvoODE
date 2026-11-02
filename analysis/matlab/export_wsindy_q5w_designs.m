function export_wsindy_q5w_designs(root, limit)
% Preserve actual reference matrices for the offline Python solver experiment.
% The production driver and external reference remain untouched.
if nargin < 1, root = pwd; end
if nargin < 2, limit = inf; end
base = fullfile(root,'outputs','sideproject_q5w_wsindy');
diagnosis = jsondecode(fileread(fullfile(base,'solver_diagnosis','diagnosis.json')));
target = fullfile(base,'matlab_designs');
if ~exist(target,'dir'), mkdir(target); end
addpath(fullfile(root,'outputs','reference_wsindy_ode_72d8d6e'));
grid = 10.^linspace(-4,0,100);
for k = 1:min(limit,numel(diagnosis.tasks))
    task = diagnosis.tasks(k);
    inputs = fullfile(base,'matlab_inputs');
    if strcmp(task.arm,'W1-interp'), inputs = fullfile(inputs,'w1_interp'); end
    data = load(fullfile(inputs,[task.cell '.mat']));
    identity = jsondecode(fileread(fullfile(inputs,[task.cell '.json'])));
    [coef,~,~,loss,~,~,~,~,~,~,Gs,bs,scaling,~,~,tags] = wsindy_ode_fun( ...
        data.xobs,data.tobs,[],[],[],data.requested_tags,{}, ...
        1,1,1e-16,-1,1,1,0,2,0,grid,0,0.8, ...
        0.8,[1;0],[1;0],0,2,ceil(numel(data.tobs)/100));
    permutation = zeros(size(data.requested_tags,1),1);
    for j = 1:numel(permutation)
        found = find(all(tags == data.requested_tags(j,:),2));
        assert(numel(found)==1,'Nonunique tag mapping');
        permutation(j) = found;
    end
    payload = struct('coef',coef,'scaling',scaling,'permutation',permutation);
    payload.time_sha256 = identity.time_sha256;
    payload.state_sha256 = identity.state_sha256;
    payload.lambda_indices = zeros(numel(Gs),1);
    for eq = 1:numel(Gs)
        payload.(sprintf('G_%d',eq-1)) = Gs{eq};
        payload.(sprintf('b_%d',eq-1)) = bs{eq};
        [~,selected] = min(loss{eq}(1,:));
        payload.lambda_indices(eq) = selected-1;
    end
    temporary = fullfile(target,[task.cell '.tmp.mat']);
    save(temporary,'-struct','payload','-v7');
    movefile(temporary,fullfile(target,[task.cell '.mat']),'f');
    fprintf('exported design %s\n',task.cell);
end
end
